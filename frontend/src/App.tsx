import {
  FormEvent,
  startTransition,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Navigate, Route, Routes, useSearchParams } from "react-router-dom";

import {
  ActivityLevel,
  ApiError,
  AnalysisHistoryDetailResponse,
  AnalysisHistoryListItem,
  AnalysisResultResponse,
  AuthMeResponse,
  CandidateDraftItem,
  GoalType,
  ProfileResponse,
  ProfileUpdateRequest,
  ThemePreference,
  apiBaseUrl,
  confirmAnalysis,
  createConsent,
  createAnalysisDraft,
  exchangeAuthToken,
  createMockImageFile,
  getAnalysisDetail,
  getAnalysisHistory,
  getProfile,
  reestimateAnalysis,
  updateProfile,
  updateThemePreference,
  uploadAnalysisImage,
} from "./api";
import {
  consentUiCopy,
  consentSections,
  type ConsentContentSection,
} from "./constants/consent";
import { LineLoginButton } from "./components/LineLoginButton";
import { RequireAuth } from "./components/RequireAuth";
import { useAuth } from "./hooks/useAuth";
import { useLogout } from "./hooks/useLogout";
import "./styles.css";

type MainScreen = "analysis" | "history" | "profile" | "consent";
type AnalysisStage = "start" | "confirm" | "result";

type ProfileFormState = {
  age: string;
  height_cm: string;
  weight_kg: string;
  activity_level: ActivityLevel;
  goal_type: GoalType;
  goal_weight_kg: string;
};

const candidateUnitOptions = [
  "g",
  "bowl",
  "plate",
  "cup",
  "pcs",
  "box",
  "bag",
  "tbsp",
] as const;

let candidateDraftSequence = 0;

function nextCandidateDraftId() {
  candidateDraftSequence += 1;
  return `candidate-${candidateDraftSequence}`;
}

const activityOptions: Array<{
  value: ActivityLevel;
  label: string;
  hint: string;
}> = [
  { value: "sedentary", label: "久坐", hint: "平常幾乎沒有運動" },
  { value: "light", label: "輕量", hint: "每週 1-2 次簡單活動" },
  { value: "moderate", label: "中等", hint: "每週固定運動 3-4 次" },
  { value: "active", label: "活躍", hint: "多數日都有訓練" },
  { value: "very_active", label: "高強度", hint: "高頻訓練或勞力活動" },
];

const goalOptions: Array<{ value: GoalType; label: string; hint: string }> = [
  { value: "fat_loss", label: "減脂", hint: "優先控制熱量與維持蛋白質" },
  { value: "muscle_gain", label: "增肌", hint: "優先維持攝取並搭配力量訓練" },
];

function profileToFormState(profile: ProfileResponse | null): ProfileFormState {
  return {
    age: profile?.profile.age?.toString() ?? "",
    height_cm: profile?.profile.height_cm?.toString() ?? "",
    weight_kg: profile?.profile.weight_kg ?? "",
    activity_level: profile?.profile.activity_level ?? "moderate",
    goal_type: profile?.profile.goal_type ?? "fat_loss",
    goal_weight_kg: profile?.profile.goal_weight_kg ?? "",
  };
}

function toCandidateDraftItems(
  result: Awaited<ReturnType<typeof uploadAnalysisImage>>["candidates"],
): CandidateDraftItem[] {
  return result.map((candidate) => ({
    id: nextCandidateDraftId(),
    is_manual: false,
    food_name: candidate.food_name,
    normalized_food_name: candidate.normalized_food_name,
    portion_value: candidate.portion_default,
    portion_unit: candidate.portion_unit,
    confidence_score: candidate.confidence_score,
  }));
}

function buildManualCandidateItem(): CandidateDraftItem {
  return {
    id: nextCandidateDraftId(),
    is_manual: true,
    food_name: "",
    normalized_food_name: "manual_entry",
    portion_value: "100",
    portion_unit: "g",
    confidence_score: null,
  };
}

function validateCandidateItems(items: CandidateDraftItem[]) {
  if (items.length === 0) {
    return "請至少保留 1 個食物，或手動新增後再送出。";
  }

  for (const item of items) {
    if (!item.food_name.trim()) {
      return "每個食物都需要名稱，請先完成空白欄位。";
    }

    const portionValue = Number(item.portion_value);
    if (!Number.isFinite(portionValue) || portionValue <= 0) {
      return "份量需要是大於 0 的數字。";
    }
  }

  return null;
}

function formatDateLabel(value: string) {
  return new Intl.DateTimeFormat("zh-TW", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function buildValidationMessage(formState: ProfileFormState) {
  if (!formState.age || !formState.height_cm || !formState.weight_kg) {
    return "請先完成年齡、身高與體重。";
  }

  return "";
}

function hasRequiredConsents(user: AuthMeResponse) {
  return user.consent_status.can_start_analysis;
}

function InlineDisclaimerNote({ body }: { body: string }) {
  return <p className="inline-disclaimer-note">{body}</p>;
}

function resolveDisclaimerCopy(
  disclaimer:
    | AnalysisResultResponse["disclaimer"]
    | AnalysisHistoryDetailResponse["disclaimer"],
) {
  if (disclaimer.consent_type === "non_medical_disclosure") {
    return consentUiCopy.disclaimerCard;
  }

  return {
    kicker: consentUiCopy.disclaimerCard.kicker,
    title: disclaimer.title,
    body: disclaimer.body,
  };
}

function ConsentAccordionCard({
  section,
  isExpanded,
  isChecked,
  version,
  onToggle,
  onCheckChange,
}: {
  section: ConsentContentSection;
  isExpanded: boolean;
  isChecked: boolean;
  version: string;
  onToggle: () => void;
  onCheckChange: (checked: boolean) => void;
}) {
  return (
    <article
      className={`panel-card consent-card ${isExpanded ? "is-expanded" : ""}`}
    >
      <button
        type="button"
        className="consent-accordion-toggle"
        aria-expanded={isExpanded}
        onClick={onToggle}
      >
        <div>
          <p className="panel-kicker">{section.kicker}</p>
          <h3>{section.title}</h3>
        </div>
        <span className="consent-accordion-icon" aria-hidden="true">
          {isExpanded ? "收合" : "展開"}
        </span>
      </button>

      <p className="consent-summary">{section.summary}</p>

      {isExpanded ? (
        <div className="consent-copy-stack">
          {section.paragraphs.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          <p className="consent-version">目前版本 {version}</p>
        </div>
      ) : null}

      <label className="consent-checkbox-row">
        <input
          type="checkbox"
          checked={isChecked}
          onChange={(event) => onCheckChange(event.currentTarget.checked)}
        />
        <span>{section.checkboxLabel}</span>
      </label>
    </article>
  );
}

function LegalReviewDialog({
  section,
  version,
  onClose,
}: {
  section: ConsentContentSection;
  version: string;
  onClose: () => void;
}) {
  const titleId = `legal-review-title-${section.id}`;

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="legal-dialog-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <section
        className="legal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="legal-dialog-header">
          <div>
            <p className="panel-kicker">{section.kicker}</p>
            <h3 id={titleId}>{section.title}</h3>
          </div>
          <button
            type="button"
            className="legal-dialog-close"
            onClick={onClose}
            aria-label="關閉隱私與聲明內容"
          >
            關閉
          </button>
        </header>

        <div className="legal-dialog-body">
          <p className="consent-summary">{section.summary}</p>
          <div className="consent-copy-stack">
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
            <p className="consent-version">目前版本 {version}</p>
          </div>
        </div>
      </section>
    </div>
  );
}

function LegalFooter({
  onOpenReview,
}: {
  onOpenReview: (sectionId: ConsentContentSection["id"]) => void;
}) {
  return (
    <footer className="legal-footer">
      <div>
        <p className="panel-kicker">{consentUiCopy.footer.kicker}</p>
        <p className="legal-footer-copy">{consentUiCopy.footer.description}</p>
      </div>
      <div className="legal-link-list" aria-label="隱私與聲明回看入口">
        {consentSections.map((section) => (
          <button
            key={section.id}
            type="button"
            className="legal-link-button"
            onClick={() => onOpenReview(section.id)}
          >
            {section.id === "privacy" ? "隱私政策" : "非醫療用途聲明"}
          </button>
        ))}
      </div>
    </footer>
  );
}

function resolveConsentSectionVersion(
  sectionId: ConsentContentSection["id"],
  user: AuthMeResponse,
) {
  return sectionId === "privacy"
    ? user.required_policy_versions.privacy_policy
    : user.required_policy_versions.non_medical_disclosure;
}

function resolveConsentSection(sectionId: ConsentContentSection["id"] | null) {
  return consentSections.find((section) => section.id === sectionId) ?? null;
}

function HomeDashboard({ user }: { user: AuthMeResponse }) {
  const queryClient = useQueryClient();
  const logoutMutation = useLogout();
  const pendingCandidateFocusId = useRef<string | null>(null);
  const [screen, setScreen] = useState<MainScreen>(
    hasRequiredConsents(user) ? "analysis" : "consent",
  );
  const [analysisStage, setAnalysisStage] = useState<AnalysisStage>("start");
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormState>(
    profileToFormState(null),
  );
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [candidateItems, setCandidateItems] = useState<CandidateDraftItem[]>(
    [],
  );
  const [analysisResult, setAnalysisResult] =
    useState<AnalysisResultResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisNotice, setAnalysisNotice] = useState<string | null>(null);
  const [reestimateNote, setReestimateNote] = useState("");
  const [reestimateSuggestions, setReestimateSuggestions] = useState<
    CandidateDraftItem[]
  >([]);
  const [reestimateLoading, setReestimateLoading] = useState(false);

  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<AnalysisHistoryListItem[]>(
    [],
  );
  const [selectedHistory, setSelectedHistory] =
    useState<AnalysisHistoryDetailResponse | null>(null);
  const [historyDetailLoading, setHistoryDetailLoading] = useState(false);
  const [consentSaving, setConsentSaving] = useState(false);
  const [consentMessage, setConsentMessage] = useState<string | null>(null);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [agreePrivacy, setAgreePrivacy] = useState(
    user.consent_status.has_privacy_policy,
  );
  const [agreeNonMedical, setAgreeNonMedical] = useState(
    user.consent_status.has_non_medical_disclosure,
  );
  const [expandedSections, setExpandedSections] = useState<
    Record<ConsentContentSection["id"], boolean>
  >({
    privacy: false,
    "non-medical": false,
  });
  const [activeLegalReview, setActiveLegalReview] = useState<
    ConsentContentSection["id"] | null
  >(null);

  const activeLegalSection = resolveConsentSection(activeLegalReview);

  useEffect(() => {
    void loadProfile();
  }, []);

  useEffect(() => {
    const hasConsents = hasRequiredConsents(user);
    if (hasConsents && screen === "consent") {
      setScreen("analysis");
    }
    if (!hasConsents && screen !== "consent") {
      setActiveLegalReview(null);
      setSelectedHistory(null);
      setScreen("consent");
    }
  }, [screen, user]);

  useEffect(() => {
    setAgreePrivacy(user.consent_status.has_privacy_policy);
    setAgreeNonMedical(user.consent_status.has_non_medical_disclosure);
  }, [user]);

  useEffect(() => {
    if (!pendingCandidateFocusId.current) {
      return;
    }

    const nextInput = document.querySelector<HTMLInputElement>(
      `input[name="candidate-food-name-${pendingCandidateFocusId.current}"]`,
    );
    nextInput?.focus();
    pendingCandidateFocusId.current = null;
  }, [candidateItems]);

  async function loadProfile() {
    setProfileLoading(true);
    setProfileError(null);

    try {
      const response = await getProfile();
      setProfile(response);
      setProfileForm(profileToFormState(response));
    } catch (error) {
      setProfileError(
        error instanceof Error ? error.message : "Profile 載入失敗",
      );
    } finally {
      setProfileLoading(false);
    }
  }

  async function loadHistory() {
    setHistoryLoading(true);
    setHistoryError(null);

    try {
      const response = await getAnalysisHistory();
      setHistoryItems(response.items);
    } catch (error) {
      setHistoryError(
        error instanceof Error ? error.message : "History 載入失敗",
      );
    } finally {
      setHistoryLoading(false);
    }
  }

  function handleMainScreenChange(nextScreen: MainScreen) {
    if (nextScreen !== "consent" && !hasRequiredConsents(user)) {
      setConsentError(consentUiCopy.message.flowRequired);
      startTransition(() => setScreen("consent"));
      return;
    }

    startTransition(() => {
      setScreen(nextScreen);
      if (nextScreen === "history") {
        void loadHistory();
      }
      if (nextScreen !== "history") {
        setSelectedHistory(null);
      }
    });
  }

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileSaving(true);
    setProfileError(null);
    setProfileMessage(null);

    try {
      const payload: ProfileUpdateRequest = {
        age: Number(profileForm.age),
        height_cm: Number(profileForm.height_cm),
        weight_kg: Number(profileForm.weight_kg),
        activity_level: profileForm.activity_level,
        goal_type: profileForm.goal_type,
        goal_weight_kg: profileForm.goal_weight_kg
          ? Number(profileForm.goal_weight_kg)
          : null,
      };
      const response = await updateProfile(payload);
      setProfile(response);
      setProfileForm(profileToFormState(response));
      setProfileMessage("Profile 已儲存，下一次分析會套用新設定。");
    } catch (error) {
      setProfileError(
        error instanceof Error ? error.message : "Profile 儲存失敗",
      );
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleThemeChange(themePreference: ThemePreference) {
    setProfileError(null);

    try {
      const response = await updateThemePreference(themePreference);
      setProfile(response);
      setProfileMessage(
        themePreference === "female_default"
          ? "已切換成柔和主題。"
          : "已切換成俐落主題。",
      );
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "主題切換失敗");
    }
  }

  async function beginAnalysis(file: File) {
    if (!user.consent_status.can_start_analysis) {
      setAnalysisError(consentUiCopy.message.analysisRequired);
      setConsentError(consentUiCopy.message.flowRequired);
      setScreen("consent");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysisNotice(null);
    setReestimateSuggestions([]);
    setReestimateNote("");

    try {
      const draft = await createAnalysisDraft();
      const candidateResponse = await uploadAnalysisImage(draft.id, file);

      setAnalysisId(candidateResponse.analysis_id);
      setAnalysisResult(null);

      if (candidateResponse.recognition_status === "complete_failure") {
        setCandidateItems([]);
        setAnalysisNotice(
          candidateResponse.message ??
            "這張照片 AI 這次沒有穩定辨識成功，請重拍或換一張更清楚的圖片。",
        );
        startTransition(() => setAnalysisStage("start"));
        return;
      }

      setCandidateItems(toCandidateDraftItems(candidateResponse.candidates));
      setAnalysisNotice(
        candidateResponse.recognition_status === "partial"
          ? (candidateResponse.message ??
              "AI 已先給一版候選，請幫我再確認名稱和份量。")
          : null,
      );
      startTransition(() => setAnalysisStage("confirm"));
    } catch (error) {
      if (error instanceof ApiError && error.code === "CONSENT_REQUIRED") {
        setConsentError(consentUiCopy.message.analysisRequired);
        setScreen("consent");
      }
      setAnalysisError(error instanceof Error ? error.message : "分析建立失敗");
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleFileInput(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) {
      return;
    }

    await beginAnalysis(file);
  }

  async function handleConfirmAnalysis() {
    if (!analysisId) {
      setAnalysisError("找不到 analysis id，請重新開始。");
      return;
    }

    const validationError = validateCandidateItems(candidateItems);
    if (validationError) {
      setAnalysisError(validationError);
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysisNotice(null);

    try {
      const response = await confirmAnalysis(analysisId, candidateItems);
      setAnalysisResult(response);
      setReestimateSuggestions([]);
      setReestimateNote("");
      startTransition(() => {
        setAnalysisStage("result");
        setScreen("analysis");
      });
      await loadHistory();
    } catch (error) {
      if (error instanceof ApiError && error.code === "CONSENT_REQUIRED") {
        setConsentError(consentUiCopy.message.confirmRequired);
        setScreen("consent");
      }
      setAnalysisError(error instanceof Error ? error.message : "確認分析失敗");
    } finally {
      setAnalysisLoading(false);
    }
  }

  function updateCandidateItem(
    candidateId: string,
    updater: (item: CandidateDraftItem) => CandidateDraftItem,
  ) {
    setCandidateItems((current) =>
      current.map((item) => (item.id === candidateId ? updater(item) : item)),
    );
  }

  function removeCandidateItem(candidateId: string) {
    setCandidateItems((current) =>
      current.filter((item) => item.id !== candidateId),
    );
    setAnalysisError(null);
  }

  function addManualCandidateItem() {
    const nextItem = buildManualCandidateItem();
    pendingCandidateFocusId.current = nextItem.id;
    setCandidateItems((current) => [...current, nextItem]);
    setAnalysisError(null);
  }

  async function handleReestimateAnalysis() {
    if (!analysisId) {
      setAnalysisError("找不到 analysis id，請重新開始。");
      return;
    }

    const validationError = validateCandidateItems(candidateItems);
    if (validationError) {
      setAnalysisError(validationError);
      return;
    }

    setReestimateLoading(true);
    setAnalysisError(null);

    try {
      const response = await reestimateAnalysis(
        analysisId,
        candidateItems,
        reestimateNote,
      );
      setReestimateSuggestions(toCandidateDraftItems(response.candidates));
      setAnalysisNotice(
        response.message ?? "AI 已根據你目前的修正重新估算，請再次確認。",
      );
    } catch (error) {
      setAnalysisError(
        error instanceof Error ? error.message : "再次請 AI 估算失敗",
      );
    } finally {
      setReestimateLoading(false);
    }
  }

  function applyReestimateSuggestions() {
    if (reestimateSuggestions.length === 0) {
      return;
    }

    setCandidateItems(reestimateSuggestions);
    setReestimateSuggestions([]);
    setAnalysisNotice("已套用 AI 新建議，你可以再檢查一次後送出確認。");
  }

  function dismissReestimateSuggestions() {
    setReestimateSuggestions([]);
    setAnalysisNotice("已保留你目前的內容，AI 建議未套用。");
  }

  async function handleHistoryDetailOpen(analysisIdToOpen: string) {
    setHistoryDetailLoading(true);
    setHistoryError(null);

    try {
      const response = await getAnalysisDetail(analysisIdToOpen);
      setSelectedHistory(response);
    } catch (error) {
      setHistoryError(
        error instanceof Error ? error.message : "History detail 載入失敗",
      );
    } finally {
      setHistoryDetailLoading(false);
    }
  }

  async function handleConsentSubmit() {
    if (!agreePrivacy || !agreeNonMedical) {
      setConsentError(consentUiCopy.message.checkboxRequired);
      return;
    }

    setConsentSaving(true);
    setConsentError(null);
    setConsentMessage(null);

    try {
      await Promise.all([
        createConsent(
          "privacy_policy",
          user.required_policy_versions.privacy_policy,
        ),
        createConsent(
          "non_medical_disclosure",
          user.required_policy_versions.non_medical_disclosure,
        ),
      ]);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      setConsentMessage(consentUiCopy.message.updated);
      startTransition(() => setScreen("analysis"));
    } catch (error) {
      setConsentError(
        error instanceof Error
          ? error.message
          : consentUiCopy.message.saveFailed,
      );
    } finally {
      setConsentSaving(false);
    }
  }

  const analysisAccessLocked = !user.consent_status.can_start_analysis;
  const canContinueConsent = agreePrivacy && agreeNonMedical;
  const consentCompleted = hasRequiredConsents(user);
  const themeMode = profile?.theme_preference ?? "female_default";
  const validationMessage = buildValidationMessage(profileForm);
  const analysisDisclaimerCopy = analysisResult
    ? resolveDisclaimerCopy(analysisResult.disclaimer)
    : null;
  const historyDisclaimerCopy = selectedHistory
    ? resolveDisclaimerCopy(selectedHistory.disclaimer)
    : null;

  const spotlightContent = useMemo(() => {
    if (screen === "consent") {
      return {
        title: consentUiCopy.spotlight.title,
        copy: consentUiCopy.spotlight.copy,
      };
    }

    if (screen === "history") {
      return {
        title: selectedHistory ? "History Detail" : "History",
        copy: selectedHistory
          ? `回看 ${selectedHistory.food_summary} 的營養結果與建議快照。`
          : "回看最近完成的分析摘要，確認總熱量與建議是否延續。",
      };
    }

    if (screen === "profile") {
      return {
        title: "Profile",
        copy:
          validationMessage ||
          "資料完整後，後續分析會直接套用這份目標與活動量設定。",
      };
    }

    if (!analysisResult) {
      return {
        title:
          analysisStage === "confirm"
            ? "Candidate Confirmation"
            : "Start Analysis",
        copy: "先完成一次分析，這裡會顯示你的總熱量與運動建議。",
      };
    }

    return {
      title:
        analysisStage === "confirm"
          ? "Candidate Confirmation"
          : "Analysis Result",
      copy: `本次總熱量 ${analysisResult.total_kcal} kcal，建議搭配 ${analysisResult.recommendation.recommended_exercises[0]?.name ?? "輕量活動"}。`,
    };
  }, [
    analysisResult,
    analysisStage,
    screen,
    selectedHistory,
    validationMessage,
  ]);

  return (
    <main className={`app-shell theme-${themeMode}`}>
      <div className="ambient-orb ambient-orb-left" aria-hidden="true" />
      <div className="ambient-orb ambient-orb-right" aria-hidden="true" />

      <section
        className={
          screen === "profile" ? "app-frame app-frame-profile" : "app-frame"
        }
      >
        <header className="topbar">
          <div>
            <p className="eyebrow">HappyMeal Step 2 MVP</p>
            <h1>從建檔到歷史回看的一條主鏈</h1>
          </div>
          <div className="topbar-actions">
            <div className="user-badge">
              <strong>{user.display_name}</strong>
              <span>{user.avatar_url ? "LINE 已連線" : "LINE 使用者"}</span>
            </div>
            <div className="backend-badge">API {apiBaseUrl}</div>
            <button
              className="ghost-button"
              disabled={logoutMutation.isPending}
              onClick={() => logoutMutation.mutate()}
            >
              {logoutMutation.isPending ? "登出中..." : "登出"}
            </button>
          </div>
        </header>

        <section className="spotlight-card">
          <div>
            <p className="spotlight-label">目前流程</p>
            <h2>{spotlightContent.title}</h2>
          </div>
          <p className="spotlight-copy">{spotlightContent.copy}</p>
        </section>

        {consentCompleted ? (
          <nav className="tab-strip" aria-label="主要導覽">
            <button
              className={
                screen === "analysis" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("analysis")}
            >
              Analysis
            </button>
            <button
              className={
                screen === "history" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("history")}
            >
              History
            </button>
            <button
              className={
                screen === "profile" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("profile")}
            >
              Profile
            </button>
          </nav>
        ) : null}

        {screen === "consent" ? (
          <section className="content-stack">
            {consentError ? (
              <p className="status-banner is-error">{consentError}</p>
            ) : null}
            {consentMessage ? (
              <p className="status-banner is-success">{consentMessage}</p>
            ) : null}

            <div className="panel-grid">
              <article className="panel-card consent-intro-card">
                <p className="panel-kicker">{consentUiCopy.introCard.kicker}</p>
                <h3>{consentUiCopy.introCard.title}</h3>
                <p>{consentUiCopy.introCard.description}</p>
              </article>

              <ConsentAccordionCard
                section={consentSections[0]}
                isExpanded={expandedSections.privacy}
                isChecked={agreePrivacy}
                version={user.required_policy_versions.privacy_policy}
                onToggle={() =>
                  setExpandedSections((current) => ({
                    ...current,
                    privacy: !current.privacy,
                  }))
                }
                onCheckChange={setAgreePrivacy}
              />

              <ConsentAccordionCard
                section={consentSections[1]}
                isExpanded={expandedSections["non-medical"]}
                isChecked={agreeNonMedical}
                version={user.required_policy_versions.non_medical_disclosure}
                onToggle={() =>
                  setExpandedSections((current) => ({
                    ...current,
                    "non-medical": !current["non-medical"],
                  }))
                }
                onCheckChange={setAgreeNonMedical}
              />
            </div>

            <div className="consent-footer-actions">
              <span className="helper-copy">
                {!canContinueConsent
                  ? consentUiCopy.helper.incomplete
                  : consentUiCopy.helper.complete}
              </span>
              <button
                className="primary-button"
                onClick={() => void handleConsentSubmit()}
                disabled={consentSaving || !canContinueConsent}
              >
                {consentSaving
                  ? consentUiCopy.action.submitting
                  : consentUiCopy.action.submit}
              </button>
            </div>
          </section>
        ) : null}

        {screen === "analysis" ? (
          <section className="content-stack">
            <div className="section-heading">
              <div>
                <p className="section-kicker">WP-08 / FE-02 to FE-04</p>
                <h2>
                  {analysisStage === "start"
                    ? "Start Analysis"
                    : analysisStage === "confirm"
                      ? "Candidate Confirmation"
                      : "Analysis Result"}
                </h2>
              </div>
              {analysisStage !== "start" ? (
                <button
                  className="ghost-button"
                  onClick={() =>
                    startTransition(() => setAnalysisStage("start"))
                  }
                >
                  重新開始
                </button>
              ) : null}
            </div>

            {analysisError ? (
              <p className="status-banner is-error">{analysisError}</p>
            ) : null}
            {analysisNotice ? (
              <p className="status-banner is-info">{analysisNotice}</p>
            ) : null}
            {analysisAccessLocked ? (
              <p className="status-banner is-error">
                {consentUiCopy.message.analysisRequired}
              </p>
            ) : null}

            {analysisStage === "start" ? (
              <div className="panel-grid">
                <article className="panel-card">
                  <p className="panel-kicker">Quick Start</p>
                  <h3>用 mock 圖片快速跑一次主流程</h3>
                  <p>
                    為了驗證 MVP，這裡保留三種示範場景，會直接打到同一組 backend
                    API。
                  </p>
                  <div className="quick-actions">
                    <button
                      className="primary-button"
                      disabled={analysisLoading || analysisAccessLocked}
                      onClick={() =>
                        void beginAnalysis(createMockImageFile("salad"))
                      }
                    >
                      上傳沙拉範例
                    </button>
                    <button
                      className="secondary-button"
                      disabled={analysisLoading || analysisAccessLocked}
                      onClick={() =>
                        void beginAnalysis(createMockImageFile("rice"))
                      }
                    >
                      上傳飯類範例
                    </button>
                    <button
                      className="secondary-button"
                      disabled={analysisLoading || analysisAccessLocked}
                      onClick={() =>
                        void beginAnalysis(createMockImageFile("salmon"))
                      }
                    >
                      上傳魚排範例
                    </button>
                  </div>
                </article>

                <article className="panel-card">
                  <p className="panel-kicker">Upload</p>
                  <h3>改用本機圖片測試</h3>
                  <label className="upload-dropzone">
                    <span>支援 JPG / PNG，分析完成後原始圖片不長期保存。</span>
                    <input
                      type="file"
                      name="analysis-image"
                      accept="image/png,image/jpeg"
                      disabled={analysisAccessLocked}
                      onChange={(event) => {
                        void handleFileInput(event.currentTarget.files);
                        event.currentTarget.value = "";
                      }}
                    />
                  </label>
                </article>

                <article className="panel-card">
                  <p className="panel-kicker">State</p>
                  <h3>分析前檢查</h3>
                  <ul className="compact-list">
                    <li>
                      {validationMessage || "Profile 已具備最小分析條件。"}
                    </li>
                    <li>
                      {analysisLoading
                        ? "正在建立 draft 並上傳圖片。"
                        : "尚未開始新的分析。"}
                    </li>
                    <li>
                      {analysisAccessLocked
                        ? consentUiCopy.message.lockedSummary
                        : consentUiCopy.message.unlockedSummary}
                    </li>
                    <li>本階段只做單次分析，不做每日累積。</li>
                  </ul>
                  {analysisAccessLocked ? (
                    <button
                      className="secondary-button"
                      onClick={() => handleMainScreenChange("consent")}
                    >
                      {consentUiCopy.action.goToConsent}
                    </button>
                  ) : null}
                </article>
              </div>
            ) : null}

            {analysisStage === "confirm" ? (
              <div className="content-stack">
                <article className="panel-card">
                  <p className="panel-kicker">Candidate Confirmation</p>
                  <h3>調整食物名稱與份量後送出確認</h3>
                  <p>
                    單位優先用 g，也可切換常見份量單位；你可以刪除誤判，
                    或手動新增 AI 漏掉的食物。
                  </p>
                </article>

                {candidateItems.length === 0 ? (
                  <article className="panel-card empty-panel-card">
                    <p className="empty-panel">
                      目前沒有候選項目。你可以重新上傳，或先手動新增食物。
                    </p>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={addManualCandidateItem}
                    >
                      新增食物
                    </button>
                  </article>
                ) : null}

                <div className="candidate-stack">
                  {candidateItems.map((item) => (
                    <article
                      className={
                        item.is_manual
                          ? "candidate-card candidate-card-manual"
                          : "candidate-card"
                      }
                      key={item.id}
                    >
                      <div className="candidate-head">
                        <div>
                          <p className="candidate-kind-label">
                            {item.is_manual ? "手動新增" : "AI 辨識候選"}
                          </p>
                          <h3>{item.food_name}</h3>
                        </div>
                        <button
                          className="candidate-remove-button"
                          type="button"
                          onClick={() => removeCandidateItem(item.id)}
                        >
                          刪除
                        </button>
                      </div>

                      <div className="field-grid candidate-edit-grid">
                        <label>
                          食物名稱
                          <input
                            name={`candidate-food-name-${item.id}`}
                            placeholder="例如：白飯、豆漿、雞腿便當"
                            value={item.food_name}
                            onChange={(event) => {
                              const nextValue = event.currentTarget.value;
                              updateCandidateItem(item.id, (currentItem) => ({
                                ...currentItem,
                                food_name: nextValue,
                              }));
                            }}
                          />
                        </label>
                        <label>
                          份量
                          <input
                            name={`candidate-portion-${item.id}`}
                            inputMode="decimal"
                            placeholder="100"
                            value={item.portion_value}
                            onChange={(event) => {
                              const nextValue = event.currentTarget.value;
                              updateCandidateItem(item.id, (currentItem) => ({
                                ...currentItem,
                                portion_value: nextValue,
                              }));
                            }}
                          />
                        </label>
                        <label>
                          單位
                          <select
                            name={`candidate-unit-${item.id}`}
                            value={item.portion_unit}
                            onChange={(event) => {
                              const nextValue = event.currentTarget.value;
                              updateCandidateItem(item.id, (currentItem) => ({
                                ...currentItem,
                                portion_unit: nextValue,
                              }));
                            }}
                          >
                            {candidateUnitOptions.map((unitOption) => (
                              <option key={unitOption} value={unitOption}>
                                {unitOption}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>

                      <div className="candidate-support-row">
                        <span className="candidate-support-copy">
                          {item.portion_unit === "g"
                            ? "系統會直接用克數計算。"
                            : "系統會盡量把這個單位換算成克。"}
                        </span>
                        {item.confidence_score ? (
                          <span className="candidate-support-copy candidate-support-copy-muted">
                            AI 已先給一版候選，你可以直接覆蓋。
                          </span>
                        ) : (
                          <span className="candidate-support-copy candidate-support-copy-muted">
                            手動新增項目會直接以你輸入的名稱與份量送出。
                          </span>
                        )}
                      </div>
                    </article>
                  ))}
                </div>

                {candidateItems.length > 0 ? (
                  <button
                    className="secondary-button add-food-button"
                    type="button"
                    onClick={addManualCandidateItem}
                  >
                    新增食物
                  </button>
                ) : null}

                <article className="panel-card reestimate-panel">
                  <p className="panel-kicker">AI 校正</p>
                  <h3>補充給 AI 的說明後重新估算</h3>
                  <p>
                    例如：我只吃半份、這不是甜不辣，是炸雞。 AI
                    只會提供新建議，不會直接覆蓋你目前的內容。
                  </p>
                  <label className="reestimate-label">
                    備註或校正說明
                    <textarea
                      name="reestimate-note"
                      placeholder="例如：主菜其實是炸雞，我只吃半份白飯。"
                      value={reestimateNote}
                      onChange={(event) =>
                        setReestimateNote(event.currentTarget.value)
                      }
                      rows={3}
                    />
                  </label>
                  <div className="footer-actions">
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={
                        reestimateLoading ||
                        analysisLoading ||
                        candidateItems.length === 0
                      }
                      onClick={() => void handleReestimateAnalysis()}
                    >
                      {reestimateLoading ? "重新估算中..." : "再次請 AI 估算"}
                    </button>
                  </div>
                </article>

                {reestimateSuggestions.length > 0 ? (
                  <article className="panel-card reestimate-panel">
                    <p className="panel-kicker">AI 新建議</p>
                    <h3>選擇是否套用這版建議</h3>
                    <div className="compact-list">
                      {reestimateSuggestions.map((item) => (
                        <p className="reestimate-suggestion-row" key={item.id}>
                          <strong>{item.food_name}</strong>
                          <span>
                            {item.portion_value} {item.portion_unit}
                          </span>
                        </p>
                      ))}
                    </div>
                    <div className="footer-actions">
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={dismissReestimateSuggestions}
                      >
                        保留目前內容
                      </button>
                      <button
                        className="primary-button"
                        type="button"
                        onClick={applyReestimateSuggestions}
                      >
                        套用 AI 建議
                      </button>
                    </div>
                  </article>
                ) : null}

                <div className="footer-actions">
                  <button
                    className="secondary-button"
                    onClick={() =>
                      startTransition(() => setAnalysisStage("start"))
                    }
                  >
                    重新分析
                  </button>
                  <button
                    className="primary-button"
                    disabled={analysisLoading || candidateItems.length === 0}
                    onClick={() => void handleConfirmAnalysis()}
                  >
                    {analysisLoading ? "確認中..." : "完成確認"}
                  </button>
                </div>
              </div>
            ) : null}

            {analysisStage === "result" ? (
              analysisResult ? (
                <div className="content-stack">
                  <div className="metric-grid">
                    <article className="metric-card">
                      <span>總熱量</span>
                      <strong>{analysisResult.total_kcal}</strong>
                      <small>kcal</small>
                    </article>
                    <article className="metric-card">
                      <span>蛋白質</span>
                      <strong>{analysisResult.total_protein_g}</strong>
                      <small>g</small>
                    </article>
                    <article className="metric-card">
                      <span>脂肪</span>
                      <strong>{analysisResult.total_fat_g}</strong>
                      <small>g</small>
                    </article>
                    <article className="metric-card">
                      <span>碳水</span>
                      <strong>{analysisResult.total_carb_g}</strong>
                      <small>g</small>
                    </article>
                  </div>

                  <div className="panel-grid">
                    <article className="panel-card">
                      <p className="panel-kicker">Food Items</p>
                      <h3>本次食物明細</h3>
                      <div className="result-list">
                        {analysisResult.items.map((item) => (
                          <div
                            key={`${item.normalized_food_name}-${item.food_name}`}
                            className="result-row"
                          >
                            <div>
                              <strong>{item.food_name}</strong>
                              <p>
                                {item.portion_value} {item.portion_unit}
                              </p>
                            </div>
                            <span>{item.kcal} kcal</span>
                          </div>
                        ))}
                      </div>
                    </article>

                    <article className="panel-card">
                      <p className="panel-kicker">Recommendation</p>
                      <h3>每日目標與推薦運動</h3>
                      {analysisDisclaimerCopy ? (
                        <InlineDisclaimerNote
                          body={analysisDisclaimerCopy.body}
                        />
                      ) : null}
                      <div className="target-grid">
                        <div>
                          <span>Target kcal</span>
                          <strong>
                            {analysisResult.recommendation.target_calories_kcal}
                          </strong>
                        </div>
                        <div>
                          <span>Target protein</span>
                          <strong>
                            {analysisResult.recommendation.target_protein_g} g
                          </strong>
                        </div>
                        <div>
                          <span>Target fat</span>
                          <strong>
                            {analysisResult.recommendation.target_fat_g} g
                          </strong>
                        </div>
                        <div>
                          <span>Target carb</span>
                          <strong>
                            {analysisResult.recommendation.target_carb_g} g
                          </strong>
                        </div>
                      </div>
                      <div className="result-list">
                        {analysisResult.recommendation.recommended_exercises.map(
                          (exercise) => (
                            <div
                              key={exercise.exercise_id}
                              className="result-row"
                            >
                              <div>
                                <strong>{exercise.name}</strong>
                                <p>
                                  {exercise.duration_minutes} 分鐘 /{" "}
                                  {exercise.category}
                                </p>
                              </div>
                              <span>{exercise.burn_estimate_kcal} kcal</span>
                            </div>
                          ),
                        )}
                      </div>
                    </article>
                  </div>

                  <div className="footer-actions">
                    <button
                      className="secondary-button"
                      onClick={() => handleMainScreenChange("history")}
                    >
                      前往 History
                    </button>
                    <button
                      className="primary-button"
                      onClick={() =>
                        startTransition(() => setAnalysisStage("start"))
                      }
                    >
                      再分析一次
                    </button>
                  </div>
                </div>
              ) : (
                <p className="empty-panel">目前還沒有完成的分析結果。</p>
              )
            ) : null}
          </section>
        ) : null}

        {screen === "history" ? (
          <section className="content-stack">
            <div className="section-heading">
              <div>
                <p className="section-kicker">WP-08 / FE-05 and FE-06</p>
                <h2>{selectedHistory ? "History Detail" : "History List"}</h2>
              </div>
              {selectedHistory ? (
                <button
                  className="ghost-button"
                  onClick={() => setSelectedHistory(null)}
                >
                  回列表
                </button>
              ) : (
                <button
                  className="ghost-button"
                  onClick={() => void loadHistory()}
                >
                  重新整理
                </button>
              )}
            </div>

            {historyError ? (
              <p className="status-banner is-error">{historyError}</p>
            ) : null}

            {!selectedHistory ? (
              historyLoading ? (
                <p className="empty-panel">History 載入中...</p>
              ) : historyItems.length === 0 ? (
                <p className="empty-panel">
                  還沒有完成的分析紀錄，先去跑一次 Analysis。
                </p>
              ) : (
                <div className="history-stack">
                  {historyItems.map((item) => (
                    <button
                      key={item.analysis_id}
                      className="history-card"
                      onClick={() =>
                        void handleHistoryDetailOpen(item.analysis_id)
                      }
                    >
                      <div>
                        <p className="history-date">
                          {formatDateLabel(item.analyzed_at)}
                        </p>
                        <h3>{item.food_summary}</h3>
                        <p>{item.recommendation_summary}</p>
                      </div>
                      <strong>{item.total_kcal} kcal</strong>
                    </button>
                  ))}
                </div>
              )
            ) : historyDetailLoading ? (
              <p className="empty-panel">History detail 載入中...</p>
            ) : (
              <div className="content-stack">
                <article className="panel-card">
                  <p className="panel-kicker">Snapshot</p>
                  <h3>{selectedHistory.food_summary}</h3>
                  <p>{formatDateLabel(selectedHistory.analyzed_at)}</p>
                </article>

                <div className="metric-grid">
                  <article className="metric-card">
                    <span>總熱量</span>
                    <strong>{selectedHistory.total_kcal}</strong>
                    <small>kcal</small>
                  </article>
                  <article className="metric-card">
                    <span>蛋白質</span>
                    <strong>{selectedHistory.total_protein_g}</strong>
                    <small>g</small>
                  </article>
                  <article className="metric-card">
                    <span>脂肪</span>
                    <strong>{selectedHistory.total_fat_g}</strong>
                    <small>g</small>
                  </article>
                  <article className="metric-card">
                    <span>碳水</span>
                    <strong>{selectedHistory.total_carb_g}</strong>
                    <small>g</small>
                  </article>
                </div>

                <div className="panel-grid">
                  <article className="panel-card">
                    <p className="panel-kicker">Food Detail</p>
                    <h3>當次食物明細</h3>
                    <div className="result-list">
                      {selectedHistory.items.map((item) => (
                        <div
                          className="result-row"
                          key={`${item.food_name}-${item.normalized_food_name}`}
                        >
                          <div>
                            <strong>{item.food_name}</strong>
                            <p>
                              {item.portion_value} {item.portion_unit}
                            </p>
                          </div>
                          <span>{item.kcal} kcal</span>
                        </div>
                      ))}
                    </div>
                  </article>

                  <article className="panel-card">
                    <p className="panel-kicker">Recommendation Snapshot</p>
                    <h3>當次建議快照</h3>
                    {historyDisclaimerCopy ? (
                      <InlineDisclaimerNote body={historyDisclaimerCopy.body} />
                    ) : null}
                    <div className="result-list">
                      {selectedHistory.recommendation.recommended_exercises.map(
                        (exercise) => (
                          <div
                            key={exercise.exercise_id}
                            className="result-row"
                          >
                            <div>
                              <strong>{exercise.name}</strong>
                              <p>
                                {exercise.duration_minutes} 分鐘 /{" "}
                                {exercise.category}
                              </p>
                            </div>
                            <span>{exercise.burn_estimate_kcal} kcal</span>
                          </div>
                        ),
                      )}
                    </div>
                  </article>
                </div>
              </div>
            )}
          </section>
        ) : null}

        {screen === "profile" ? (
          <section className="content-stack">
            <div className="section-heading">
              <div>
                <p className="section-kicker">WP-08 / FE-01 and FE-07</p>
                <h2>Profile Edit</h2>
              </div>
              <button
                className="ghost-button"
                onClick={() => void loadProfile()}
              >
                重新載入
              </button>
            </div>

            {profileError ? (
              <p className="status-banner is-error">{profileError}</p>
            ) : null}
            {profileMessage ? (
              <p className="status-banner is-success">{profileMessage}</p>
            ) : null}

            {profileLoading ? (
              <p className="empty-panel">Profile 載入中...</p>
            ) : (
              <div className="panel-grid profile-layout">
                <form
                  className="panel-card profile-form"
                  onSubmit={handleProfileSubmit}
                >
                  <p className="panel-kicker">Profile Edit</p>
                  <h3>更新身體資料與目標</h3>

                  <div className="field-grid field-grid-wide">
                    <label>
                      年齡
                      <input
                        name="age"
                        value={profileForm.age}
                        inputMode="numeric"
                        onChange={(event) => {
                          const nextValue = event.currentTarget.value;
                          setProfileForm((current) => ({
                            ...current,
                            age: nextValue,
                          }));
                        }}
                      />
                    </label>
                    <label>
                      身高 cm
                      <input
                        name="height_cm"
                        value={profileForm.height_cm}
                        inputMode="numeric"
                        onChange={(event) => {
                          const nextValue = event.currentTarget.value;
                          setProfileForm((current) => ({
                            ...current,
                            height_cm: nextValue,
                          }));
                        }}
                      />
                    </label>
                    <label>
                      體重 kg
                      <input
                        name="weight_kg"
                        value={profileForm.weight_kg}
                        inputMode="decimal"
                        onChange={(event) => {
                          const nextValue = event.currentTarget.value;
                          setProfileForm((current) => ({
                            ...current,
                            weight_kg: nextValue,
                          }));
                        }}
                      />
                    </label>
                    <label>
                      目標體重 kg
                      <input
                        name="goal_weight_kg"
                        value={profileForm.goal_weight_kg}
                        inputMode="decimal"
                        onChange={(event) => {
                          const nextValue = event.currentTarget.value;
                          setProfileForm((current) => ({
                            ...current,
                            goal_weight_kg: nextValue,
                          }));
                        }}
                      />
                    </label>
                  </div>

                  <div className="choice-grid">
                    {activityOptions.map((option) => (
                      <button
                        type="button"
                        key={option.value}
                        className={
                          profileForm.activity_level === option.value
                            ? "choice-card is-active"
                            : "choice-card"
                        }
                        onClick={() =>
                          setProfileForm((current) => ({
                            ...current,
                            activity_level: option.value,
                          }))
                        }
                      >
                        <strong>{option.label}</strong>
                        <span>{option.hint}</span>
                      </button>
                    ))}
                  </div>

                  <div className="choice-grid two-columns">
                    {goalOptions.map((option) => (
                      <button
                        type="button"
                        key={option.value}
                        className={
                          profileForm.goal_type === option.value
                            ? "choice-card is-active"
                            : "choice-card"
                        }
                        onClick={() =>
                          setProfileForm((current) => ({
                            ...current,
                            goal_type: option.value,
                          }))
                        }
                      >
                        <strong>{option.label}</strong>
                        <span>{option.hint}</span>
                      </button>
                    ))}
                  </div>

                  <div className="footer-actions">
                    <span className="helper-copy">
                      {validationMessage ||
                        "資料完整後，推薦熱量與運動會依這份設定更新。"}
                    </span>
                    <button
                      className="primary-button"
                      type="submit"
                      disabled={profileSaving}
                    >
                      {profileSaving ? "儲存中..." : "儲存設定"}
                    </button>
                  </div>
                </form>

                <aside className="panel-card side-summary">
                  <p className="panel-kicker">Theme Preference</p>
                  <h3>切換視覺主題</h3>
                  <div className="choice-grid two-columns">
                    <button
                      type="button"
                      className={
                        themeMode === "female_default"
                          ? "theme-swatch is-active theme-soft"
                          : "theme-swatch theme-soft"
                      }
                      onClick={() => void handleThemeChange("female_default")}
                    >
                      <strong>柔和主題</strong>
                      <span>留白大、節奏慢、顏色柔軟</span>
                    </button>
                    <button
                      type="button"
                      className={
                        themeMode === "male_default"
                          ? "theme-swatch is-active theme-sharp"
                          : "theme-swatch theme-sharp"
                      }
                      onClick={() => void handleThemeChange("male_default")}
                    >
                      <strong>俐落主題</strong>
                      <span>對比高、字重直接、指標明確</span>
                    </button>
                  </div>
                  <div className="summary-card">
                    <span>目前使用者</span>
                    <strong>
                      {profile?.display_name ?? user.display_name}
                    </strong>
                    <p>目前已改成以 LINE Login session 驗證登入狀態。</p>
                  </div>
                  <div className="summary-card">
                    <span>{consentUiCopy.profileStatus.label}</span>
                    <strong>
                      {user.consent_status.can_start_analysis
                        ? consentUiCopy.profileStatus.completed
                        : consentUiCopy.profileStatus.pending}
                    </strong>
                    <p>
                      {user.consent_status.can_start_analysis
                        ? consentUiCopy.message.profileReady
                        : consentUiCopy.message.profilePending}
                    </p>
                    {!user.consent_status.can_start_analysis ? (
                      <button
                        className="secondary-button"
                        onClick={() => handleMainScreenChange("consent")}
                      >
                        {consentUiCopy.action.goToConsent}
                      </button>
                    ) : null}
                  </div>
                </aside>
              </div>
            )}
          </section>
        ) : null}
        {consentCompleted ? (
          <LegalFooter onOpenReview={setActiveLegalReview} />
        ) : null}
        {consentCompleted && activeLegalSection ? (
          <LegalReviewDialog
            section={activeLegalSection}
            version={resolveConsentSectionVersion(activeLegalSection.id, user)}
            onClose={() => setActiveLegalReview(null)}
          />
        ) : null}
      </section>
    </main>
  );
}

function LandingPage() {
  const { user, isLoading } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const error = searchParams.get("error");
  const token = searchParams.get("token");
  const [isExchanging, setIsExchanging] = useState(false);
  const [exchangeError, setExchangeError] = useState(false);

  useEffect(() => {
    if (!token) return;
    setIsExchanging(true);
    exchangeAuthToken(token)
      .then(() => {
        setSearchParams({}, { replace: true });
        return queryClient.invalidateQueries({ queryKey: ["me"] });
      })
      .catch(() => {
        setExchangeError(true);
        setSearchParams({}, { replace: true });
      })
      .finally(() => {
        setIsExchanging(false);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading || isExchanging) {
    return (
      <main className="auth-state-screen">
        <section className="auth-state-card">
          <p className="eyebrow">HappyMeal</p>
          <h1>登入狀態確認中</h1>
          <p>正在確認你的 LINE session，請稍候。</p>
        </section>
      </main>
    );
  }

  if (user) {
    return <Navigate to="/home" replace />;
  }

  return (
    <main className="app-shell">
      <div className="ambient-orb ambient-orb-left" aria-hidden="true" />
      <div className="ambient-orb ambient-orb-right" aria-hidden="true" />

      <section className="app-frame landing-frame">
        <header className="topbar landing-topbar">
          <div>
            <p className="eyebrow">HappyMeal</p>
            <h1>先登入，再開始你的飲食分析流程</h1>
          </div>
          <div className="backend-badge">API {apiBaseUrl}</div>
        </header>

        <section className="landing-hero">
          <article className="landing-card landing-card-primary">
            <p className="spotlight-label">LINE Login</p>
            <h2>用單一登入入口接上 session 驗證</h2>
            <p className="landing-copy">
              登入後會直接回到 /home，前端用 /auth/me 讀取你的登入狀態，
              不在瀏覽器保存 LINE access token。
            </p>
            {error === "line_auth_denied" ? (
              <p className="status-banner is-error">
                你剛剛取消了 LINE 授權，需要時可以重新登入。
              </p>
            ) : null}
            {exchangeError ? (
              <p className="status-banner is-error">
                登入連結已失效，請重新登入。
              </p>
            ) : null}
            <div className="landing-actions">
              <LineLoginButton />
            </div>
          </article>

          <article className="landing-card">
            <p className="panel-kicker">驗收重點</p>
            <h3>這一輪前端會確認三件事</h3>
            <ul className="compact-list">
              <li>未登入直接進 /home 會被導回登入頁。</li>
              <li>登入後 /auth/me 能讀到 display name 與主題設定。</li>
              <li>登出後 session 會清掉，畫面回到 /。</li>
            </ul>
          </article>
        </section>
      </section>
    </main>
  );
}

function HomeRoute() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return <HomeDashboard user={user} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomeRoute />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
