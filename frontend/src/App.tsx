type ReestimatePreviewVersion = "current" | "suggested";
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
  confirmAnalysis,
  createConsent,
  createAnalysisDraft,
  exchangeAuthToken,
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
type AnalysisLoadingPhase = "idle" | "preparing" | "recognizing";
type AnalysisLoadingSource = "mock" | "upload";

type AnalysisLoadingContext = {
  source: AnalysisLoadingSource;
  label: string;
};

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

const candidateUnitLabels: Record<
  (typeof candidateUnitOptions)[number],
  string
> = {
  g: "克",
  bowl: "碗",
  plate: "盤",
  cup: "杯",
  pcs: "個",
  box: "盒",
  bag: "袋",
  tbsp: "湯匙",
};

let candidateDraftSequence = 0;

function nextCandidateDraftId() {
  candidateDraftSequence += 1;
  return `candidate-${candidateDraftSequence}`;
}

function formatPortionUnit(unit: string) {
  return candidateUnitLabels[unit as keyof typeof candidateUnitLabels] ?? unit;
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

function buildPreviewCandidateItems(): CandidateDraftItem[] {
  return [
    {
      id: nextCandidateDraftId(),
      is_manual: false,
      food_name: "雞胸便當",
      normalized_food_name: "chicken_bento",
      portion_value: "1",
      portion_unit: "box",
      confidence_score: "0.91",
    },
    {
      id: nextCandidateDraftId(),
      is_manual: false,
      food_name: "無糖豆漿",
      normalized_food_name: "soy_milk_unsweetened",
      portion_value: "350",
      portion_unit: "g",
      confidence_score: "0.54",
    },
    {
      id: nextCandidateDraftId(),
      is_manual: true,
      food_name: "水煮蛋",
      normalized_food_name: "manual_entry",
      portion_value: "2",
      portion_unit: "pcs",
      confidence_score: null,
    },
  ];
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

function AnalysisLoadingState({
  phase,
  context,
}: {
  phase: Exclude<AnalysisLoadingPhase, "idle">;
  context: AnalysisLoadingContext;
}) {
  const stepIndex = phase === "preparing" ? 1 : 2;
  const steps = ["收到圖片", "AI 辨識", "準備候選"];
  const heading =
    phase === "preparing"
      ? "照片已收到，準備開始分析"
      : "AI 正在讀取這張餐點照片";
  const body =
    phase === "preparing"
      ? "先幫你建立這次分析，接著會把圖片送進辨識流程。整段通常只需要幾秒鐘。"
      : "我們正在整理可能的食物候選。完成後會直接帶你進入候選確認，你仍可以手動修正名稱與份量。";

  return (
    <div className="analysis-loading-shell" aria-live="polite" aria-busy="true">
      <article className="panel-card analysis-loading-hero">
        <div className="analysis-loading-hero-copy">
          <div className="analysis-loading-hero-top">
            <h3>{heading}</h3>
            <span className="analysis-loading-badge">
              <span
                className="analysis-loading-status-dot"
                aria-hidden="true"
              />
              {context.source === "upload" ? "照片辨識中" : "示範流程執行中"}
            </span>
          </div>
          <p className="analysis-loading-copy">{body}</p>
        </div>

        <div className="analysis-loading-step-row" aria-label="分析進度">
          {steps.map((step, index) => {
            const isCompleted = index < stepIndex;
            const isCurrent = index === stepIndex;

            return (
              <div
                className={[
                  "analysis-loading-step",
                  isCompleted ? "is-completed" : "",
                  isCurrent ? "is-current" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                key={step}
              >
                <span className="analysis-loading-step-index">{index + 1}</span>
                <span className="analysis-loading-step-label">{step}</span>
              </div>
            );
          })}
        </div>
      </article>
    </div>
  );
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
    inlineBody: disclaimer.body,
    body: disclaimer.body,
  };
}

function ConsentAccordionCard({
  section,
  isExpanded,
  isChecked,
  showError,
  errorMessage,
  version,
  onToggle,
  onCheckChange,
}: {
  section: ConsentContentSection;
  isExpanded: boolean;
  isChecked: boolean;
  showError: boolean;
  errorMessage: string;
  version: string;
  onToggle: () => void;
  onCheckChange: (checked: boolean) => void;
}) {
  const errorId = `consent-${section.id}-error`;

  return (
    <article
      className={`panel-card consent-card ${isExpanded ? "is-expanded" : ""} ${
        showError ? "has-error" : ""
      }`}
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
          aria-invalid={showError}
          aria-describedby={showError ? errorId : undefined}
          onChange={(event) => onCheckChange(event.currentTarget.checked)}
        />
        <span>{section.checkboxLabel}</span>
      </label>
      {showError ? (
        <p className="consent-inline-error" id={errorId} role="alert">
          {errorMessage}
        </p>
      ) : null}
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
  const dialogRef = useRef<HTMLElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    previousFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const previousBodyOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus({ preventScroll: true });

    const focusableSelector = [
      "button:not([disabled])",
      "[href]",
      "input:not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
    ].join(", ");

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const dialog = dialogRef.current;
      if (!dialog) {
        return;
      }

      const focusableElements = Array.from(
        dialog.querySelectorAll<HTMLElement>(focusableSelector),
      ).filter((element) => element.offsetParent !== null);

      if (focusableElements.length === 0) {
        event.preventDefault();
        dialog.focus({ preventScroll: true });
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus({ preventScroll: true });
        return;
      }

      if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus({ preventScroll: true });
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousBodyOverflow;
      previousFocusRef.current?.focus({ preventScroll: true });
    };
  }, [onClose]);

  return (
    <div
      className="legal-dialog-backdrop"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        ref={dialogRef}
        className="legal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="legal-dialog-header">
          <div>
            <p className="panel-kicker">{section.kicker}</p>
            <h3 id={titleId}>{section.title}</h3>
          </div>
          <button
            ref={closeButtonRef}
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
  const [searchParams] = useSearchParams();
  const pendingCandidateFocusId = useRef<string | null>(null);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
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
  const [analysisLoadingPhase, setAnalysisLoadingPhase] =
    useState<AnalysisLoadingPhase>("idle");
  const [analysisLoadingContext, setAnalysisLoadingContext] =
    useState<AnalysisLoadingContext>({
      source: "upload",
      label: "這次的照片",
    });
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisNotice, setAnalysisNotice] = useState<string | null>(null);
  const [reestimateNote, setReestimateNote] = useState("");
  const [reestimateExpanded, setReestimateExpanded] = useState(false);
  const [reestimatePreviewVersion, setReestimatePreviewVersion] =
    useState<ReestimatePreviewVersion>("current");
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
  const [consentSubmitAttempted, setConsentSubmitAttempted] = useState(false);
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
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const previewMode = searchParams.get("preview");

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
      setIsUserMenuOpen(false);
      setScreen("consent");
    }
  }, [screen, user]);

  useEffect(() => {
    setAgreePrivacy(user.consent_status.has_privacy_policy);
    setAgreeNonMedical(user.consent_status.has_non_medical_disclosure);
  }, [user]);

  useEffect(() => {
    if (previewMode === "analysis-loading") {
      setScreen("analysis");
      setAnalysisStage("start");
      setAnalysisLoading(true);
      setAnalysisLoadingPhase("recognizing");
      setAnalysisLoadingContext({
        source: "upload",
        label: "preview-analysis.jpg",
      });
      setAnalysisId(null);
      setCandidateItems([]);
      setAnalysisResult(null);
      setAnalysisError(null);
      setAnalysisNotice(
        "預覽模式：固定顯示分析中畫面。移除網址中的 preview 參數即可回到正常流程。",
      );
      setReestimateExpanded(false);
      setReestimateSuggestions([]);
      setReestimateNote("");
      return;
    }

    if (previewMode === "candidate") {
      let isCancelled = false;

      setScreen("analysis");
      setAnalysisLoading(false);
      setAnalysisLoadingPhase("idle");
      setAnalysisLoadingContext({
        source: "upload",
        label: "preview-analysis.jpg",
      });
      setAnalysisId("preview-analysis");
      setCandidateItems(buildPreviewCandidateItems());
      setAnalysisError(null);
      setReestimateExpanded(false);
      setReestimateSuggestions([]);
      setReestimateNote("");

      void (async () => {
        try {
          const response = await getAnalysisDetail("preview-analysis");
          if (isCancelled) {
            return;
          }

          if (response.status === "completed") {
            setAnalysisStage("result");
            setAnalysisResult(response);
            setAnalysisNotice(
              "預覽模式：固定顯示完成後結果頁。移除網址中的 preview 參數即可回到正常流程。",
            );
            return;
          }

          setAnalysisStage("confirm");
          setAnalysisResult(null);
          setAnalysisNotice(
            "預覽模式：固定顯示候選確認頁。移除網址中的 preview 參數即可回到正常流程。",
          );
        } catch {
          if (isCancelled) {
            return;
          }

          setAnalysisStage("confirm");
          setAnalysisResult(null);
          setAnalysisNotice(
            "預覽模式：固定顯示候選確認頁。移除網址中的 preview 參數即可回到正常流程。",
          );
        }
      })();

      return () => {
        isCancelled = true;
      };
    }
  }, [previewMode]);

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
        error instanceof Error ? error.message : "個人資料載入失敗",
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
      setHistoryError(error instanceof Error ? error.message : "紀錄載入失敗");
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
      setProfileMessage("個人資料已儲存，下一次分析會套用新設定。");
    } catch (error) {
      setProfileError(
        error instanceof Error ? error.message : "個人資料儲存失敗",
      );
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleThemeChange(themePreference: ThemePreference) {
    setProfileError(null);
    setProfileMessage(null);

    try {
      const response = await updateThemePreference(themePreference);
      setProfile(response);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "主題切換失敗");
    }
  }

  async function beginAnalysis(file: File, context?: AnalysisLoadingContext) {
    if (!user.consent_status.can_start_analysis) {
      setAnalysisError(consentUiCopy.message.analysisRequired);
      setConsentError(consentUiCopy.message.flowRequired);
      setScreen("consent");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisLoadingPhase("preparing");
    setAnalysisLoadingContext(
      context ?? {
        source: "upload",
        label: file.name || "這次的照片",
      },
    );
    setAnalysisError(null);
    setAnalysisNotice(null);
    setReestimateExpanded(false);
    setReestimateSuggestions([]);
    setReestimateNote("");

    try {
      const draft = await createAnalysisDraft();
      setAnalysisLoadingPhase("recognizing");
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
      setAnalysisLoadingPhase("idle");
      setReestimatePreviewVersion("current");
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
      setAnalysisError("找不到這次的分析，請重新開始。");
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
      setReestimateExpanded(false);
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
      setAnalysisError("找不到這次的分析，請重新開始。");
      return;
    }

    const validationError = validateCandidateItems(candidateItems);
    if (validationError) {
      setAnalysisError(validationError);
      return;
    }

    setReestimateLoading(true);
    setReestimateExpanded(false);
    setAnalysisError(null);

    try {
      const response = await reestimateAnalysis(
        analysisId,
        candidateItems,
        reestimateNote,
      );
      setReestimateSuggestions(toCandidateDraftItems(response.candidates));
      setReestimatePreviewVersion("suggested");
      setReestimateExpanded(false);
      setAnalysisNotice(
        response.message ?? "AI 已根據你目前的修正重新估算，請再次確認。",
      );
    } catch {
      setAnalysisError(
        "AI 重新估算失敗，你目前的修改都已保留，可以繼續手動調整或直接送出確認。",
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
    setReestimatePreviewVersion("current");
    setReestimateExpanded(false);
    setReestimateSuggestions([]);
    setReestimateNote("");
    setAnalysisNotice("已套用 AI 新建議，你可以再檢查一次後送出確認。");
  }

  function dismissReestimateSuggestions() {
    setReestimatePreviewVersion("current");
    setReestimateExpanded(false);
    setReestimateSuggestions([]);
    setReestimateNote("");
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
    setConsentSubmitAttempted(true);

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
      setConsentSubmitAttempted(false);
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
  const showPrivacyConsentError = consentSubmitAttempted && !agreePrivacy;
  const showNonMedicalConsentError = consentSubmitAttempted && !agreeNonMedical;
  const reestimatePreviewItems =
    reestimatePreviewVersion === "suggested"
      ? reestimateSuggestions
      : candidateItems;
  const reestimatePreviewTitle =
    reestimatePreviewVersion === "suggested" ? "新的內容" : "目前內容";
  const reestimatePreviewDescription =
    reestimatePreviewVersion === "suggested"
      ? "這是根據你的補充重新整理的一版，確認後再決定要不要改用它。"
      : "這是你目前保留的版本。若想回頭看新的內容，再切換過去即可。";
  const consentCompleted = hasRequiredConsents(user);
  const themeMode = profile?.theme_preference ?? "female_default";
  const validationMessage = buildValidationMessage(profileForm);
  const isRecommendationProfileIncomplete =
    profile === null ||
    profile.profile.weight_kg === null ||
    profile.profile.activity_level === null ||
    profile.profile.goal_type === null;
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
        title: selectedHistory ? "分析詳情" : "分析紀錄",
        copy: selectedHistory
          ? `回看 ${selectedHistory.food_summary} 的營養結果與建議快照。`
          : "回看最近完成的分析摘要，確認總熱量與建議是否延續。",
      };
    }

    if (screen === "profile") {
      return {
        title: "個人資料",
        copy:
          validationMessage ||
          "資料完整後，後續分析會直接套用這份目標與活動量設定。",
      };
    }

    if (!analysisResult) {
      return {
        title: analysisStage === "confirm" ? "候選確認" : "開始分析",
        copy: "先完成一次分析，這裡會顯示你的總熱量與運動建議。",
      };
    }

    return {
      title: analysisStage === "confirm" ? "候選確認" : "分析結果",
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
          <p className="eyebrow topbar-brand">HappyMeal</p>
          <div className="topbar-actions">
            <div className="user-menu">
              <button
                type="button"
                className="user-badge user-badge-trigger"
                aria-expanded={isUserMenuOpen}
                aria-haspopup="menu"
                onClick={() => setIsUserMenuOpen((open) => !open)}
              >
                <span className="user-badge-copy">
                  <strong>{user.display_name}</strong>
                </span>
              </button>
              {isUserMenuOpen ? (
                <div className="user-menu-popover" role="menu">
                  <button
                    className="ghost-button user-menu-action"
                    disabled={logoutMutation.isPending}
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      logoutMutation.mutate();
                    }}
                  >
                    {logoutMutation.isPending ? "登出中..." : "登出"}
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        {consentCompleted ? (
          <nav className="tab-strip tab-strip-floating" aria-label="主要導覽">
            <button
              className={
                screen === "analysis" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("analysis")}
            >
              分析
            </button>
            <button
              className={
                screen === "history" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("history")}
            >
              紀錄
            </button>
            <button
              className={
                screen === "profile" ? "tab-chip is-active" : "tab-chip"
              }
              onClick={() => handleMainScreenChange("profile")}
            >
              設定
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
                showError={showPrivacyConsentError}
                errorMessage={consentUiCopy.inlineError.privacy}
                version={user.required_policy_versions.privacy_policy}
                onToggle={() =>
                  setExpandedSections((current) => ({
                    ...current,
                    privacy: !current.privacy,
                  }))
                }
                onCheckChange={(checked) => {
                  setAgreePrivacy(checked);
                  setConsentError(null);
                }}
              />

              <ConsentAccordionCard
                section={consentSections[1]}
                isExpanded={expandedSections["non-medical"]}
                isChecked={agreeNonMedical}
                showError={showNonMedicalConsentError}
                errorMessage={consentUiCopy.inlineError.nonMedical}
                version={user.required_policy_versions.non_medical_disclosure}
                onToggle={() =>
                  setExpandedSections((current) => ({
                    ...current,
                    "non-medical": !current["non-medical"],
                  }))
                }
                onCheckChange={(checked) => {
                  setAgreeNonMedical(checked);
                  setConsentError(null);
                }}
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
                disabled={consentSaving}
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
                <h2>
                  {analysisStage === "start"
                    ? "開始分析"
                    : analysisStage === "confirm"
                      ? "候選確認"
                      : "分析結果"}
                </h2>
              </div>
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
              analysisLoading ? (
                <AnalysisLoadingState
                  phase={
                    analysisLoadingPhase === "idle"
                      ? "preparing"
                      : analysisLoadingPhase
                  }
                  context={analysisLoadingContext}
                />
              ) : (
                <div className="panel-grid start-analysis-grid">
                  <button
                    className="primary-button start-analysis-upload-button"
                    type="button"
                    disabled={analysisLoading || analysisAccessLocked}
                    onClick={() => uploadInputRef.current?.click()}
                  >
                    上傳圖片
                  </button>
                  <input
                    ref={uploadInputRef}
                    className="upload-dropzone-input"
                    type="file"
                    name="analysis-image"
                    accept="image/png,image/jpeg"
                    disabled={analysisLoading || analysisAccessLocked}
                    onChange={(event) => {
                      void handleFileInput(event.currentTarget.files);
                      event.currentTarget.value = "";
                    }}
                  />

                  <div
                    className="legal-link-list start-analysis-legal-list"
                    aria-label="分析前檢查聲明入口"
                  >
                    {consentSections.map((section) => (
                      <button
                        key={section.id}
                        type="button"
                        className="legal-link-button"
                        onClick={() => setActiveLegalReview(section.id)}
                      >
                        {section.id === "privacy"
                          ? "隱私政策"
                          : "非醫療用途聲明"}
                      </button>
                    ))}
                  </div>
                </div>
              )
            ) : null}

            {analysisStage === "confirm" ? (
              <div className="content-stack">
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
                      className={[
                        "candidate-card",
                        item.is_manual ? "candidate-card-manual" : "",
                        !item.is_manual &&
                        item.confidence_score !== null &&
                        item.confidence_score !== undefined &&
                        Number(item.confidence_score) < 0.6
                          ? "is-low-confidence"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      key={item.id}
                    >
                      <div className="candidate-head">
                        <div className="candidate-title-block">
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

                      <div className="candidate-edit-grid">
                        <label className="candidate-field candidate-field-name">
                          <span className="candidate-field-label">
                            食物名稱
                          </span>
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
                        <div className="candidate-inline-fields">
                          <label className="candidate-field candidate-field-compact">
                            <span className="candidate-field-label">份量</span>
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
                          <label className="candidate-field candidate-field-compact">
                            <span className="candidate-field-label">單位</span>
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
                                  {formatPortionUnit(unitOption)}
                                </option>
                              ))}
                            </select>
                          </label>
                        </div>
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

                {reestimateLoading ? (
                  <article className="panel-card reestimate-loading-card">
                    <span
                      className="analysis-loading-status-dot"
                      aria-hidden="true"
                    />
                    AI 重新估算中，請稍候…
                  </article>
                ) : null}

                {reestimateExpanded ? (
                  <>
                    <div
                      className="reestimate-overlay"
                      aria-hidden="true"
                      onClick={() => {
                        if (!reestimateLoading) {
                          setReestimateExpanded(false);
                          setAnalysisError(null);
                        }
                      }}
                    />
                    <div
                      className="reestimate-bottom-sheet"
                      role="dialog"
                      aria-label="AI 重新估算"
                      aria-modal="true"
                    >
                      <div
                        className="reestimate-bottom-sheet-handle"
                        aria-hidden="true"
                      />
                      <div className="reestimate-bottom-sheet-header">
                        <div>
                          <p className="panel-kicker">Optional AI Review</p>
                          <h3>補充描述給 AI</h3>
                        </div>
                        <button
                          className="ghost-button"
                          type="button"
                          disabled={reestimateLoading}
                          onClick={() => {
                            setReestimateExpanded(false);
                            setAnalysisError(null);
                          }}
                        >
                          關閉
                        </button>
                      </div>
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
                          className="primary-button"
                          type="button"
                          disabled={
                            reestimateLoading ||
                            analysisLoading ||
                            candidateItems.length === 0 ||
                            !reestimateNote.trim()
                          }
                          onClick={() => void handleReestimateAnalysis()}
                        >
                          {reestimateLoading ? "估算中..." : "送出給 AI"}
                        </button>
                      </div>
                    </div>
                  </>
                ) : null}

                {reestimateSuggestions.length > 0 ? (
                  <article className="panel-card reestimate-panel">
                    <p className="panel-kicker">AI 新建議</p>
                    <h3>切換查看你要用哪一個版本</h3>
                    <div
                      className="reestimate-preview-toggle"
                      role="tablist"
                      aria-label="AI 建議版本切換"
                    >
                      <button
                        className={`reestimate-preview-tab${
                          reestimatePreviewVersion === "current"
                            ? " is-active"
                            : ""
                        }`}
                        type="button"
                        role="tab"
                        aria-selected={reestimatePreviewVersion === "current"}
                        onClick={() => setReestimatePreviewVersion("current")}
                      >
                        目前內容
                      </button>
                      <button
                        className={`reestimate-preview-tab${
                          reestimatePreviewVersion === "suggested"
                            ? " is-active"
                            : ""
                        }`}
                        type="button"
                        role="tab"
                        aria-selected={reestimatePreviewVersion === "suggested"}
                        onClick={() => setReestimatePreviewVersion("suggested")}
                      >
                        新的內容
                      </button>
                    </div>
                    <div className="reestimate-preview-card">
                      <div className="reestimate-preview-header">
                        <strong>{reestimatePreviewTitle}</strong>
                        <span>{reestimatePreviewDescription}</span>
                      </div>
                      <div className="compact-list">
                        {reestimatePreviewItems.map((item) => (
                          <p
                            className="reestimate-suggestion-row"
                            key={item.id}
                          >
                            <strong>{item.food_name}</strong>
                            <span>
                              {item.portion_value}{" "}
                              {formatPortionUnit(item.portion_unit)}
                            </span>
                          </p>
                        ))}
                      </div>
                    </div>
                    <div className="reestimate-secondary-actions">
                      <button
                        className="inline-text-button"
                        type="button"
                        onClick={() => {
                          setReestimateSuggestions([]);
                          setReestimateExpanded(true);
                          setAnalysisNotice(null);
                        }}
                      >
                        內容還是不對，重新補充描述
                      </button>
                    </div>
                    <div className="reestimate-action-bar">
                      <button
                        className="secondary-button reestimate-action-secondary"
                        type="button"
                        onClick={dismissReestimateSuggestions}
                      >
                        保留目前內容
                      </button>
                      <button
                        className="primary-button reestimate-action-primary"
                        type="button"
                        onClick={applyReestimateSuggestions}
                      >
                        改用新的內容
                      </button>
                    </div>
                  </article>
                ) : null}

                {reestimateSuggestions.length === 0 && !reestimateLoading ? (
                  <div className="candidate-secondary-actions">
                    <button
                      className="secondary-button candidate-secondary-action-button"
                      type="button"
                      onClick={() =>
                        startTransition(() => setAnalysisStage("start"))
                      }
                    >
                      換張照片
                    </button>
                    <button
                      className="secondary-button candidate-secondary-action-button"
                      type="button"
                      disabled={analysisLoading || candidateItems.length === 0}
                      onClick={() => {
                        setReestimateExpanded(true);
                        setAnalysisError(null);
                      }}
                    >
                      請 AI 重新估算
                    </button>
                  </div>
                ) : null}

                <div className="footer-actions footer-actions-primary-only">
                  <button
                    className="primary-button"
                    disabled={analysisLoading || candidateItems.length === 0}
                    onClick={() => void handleConfirmAnalysis()}
                  >
                    {analysisLoading ? "確認中..." : "完成確認"}
                  </button>
                </div>

                {isRecommendationProfileIncomplete ? (
                  <div className="status-banner is-warning">
                    <strong>這次會先產生通用建議</strong>
                    <span>
                      補完個人資料後，系統可以提供更貼近你的每日目標與活動建議。
                    </span>
                    <button
                      className="inline-text-button"
                      type="button"
                      onClick={() =>
                        startTransition(() => setScreen("profile"))
                      }
                    >
                      前往填寫 profile
                    </button>
                  </div>
                ) : null}
              </div>
            ) : null}

            {analysisStage === "result" ? (
              analysisResult ? (
                <div className="content-stack">
                  <article className="panel-card result-summary-panel">
                    <div className="result-summary-list">
                      {[
                        {
                          label: "總熱量",
                          value: analysisResult.total_kcal,
                          unit: "kcal",
                        },
                        {
                          label: "蛋白質",
                          value: analysisResult.total_protein_g,
                          unit: "g",
                        },
                        {
                          label: "脂肪",
                          value: analysisResult.total_fat_g,
                          unit: "g",
                        },
                        {
                          label: "碳水",
                          value: analysisResult.total_carb_g,
                          unit: "g",
                        },
                      ].map((metric) => (
                        <div
                          className="result-row result-summary-row"
                          key={metric.label}
                        >
                          <div>
                            <strong>{metric.label}</strong>
                          </div>
                          <span>
                            {metric.value} {metric.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  </article>

                  <div className="panel-grid">
                    <article className="panel-card">
                      <div className="result-list">
                        {analysisResult.items.map((item) => (
                          <div
                            key={`${item.normalized_food_name}-${item.food_name}`}
                            className="result-row"
                          >
                            <div>
                              <strong>{item.food_name}</strong>
                              <p>
                                {item.portion_value}{" "}
                                {formatPortionUnit(item.portion_unit)}
                              </p>
                            </div>
                            <span>{item.kcal} kcal</span>
                          </div>
                        ))}
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
                <h2>{selectedHistory ? "分析詳情" : "分析紀錄"}</h2>
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
                <p className="empty-panel">載入中...</p>
              ) : historyItems.length === 0 ? (
                <p className="empty-panel">
                  還沒有分析紀錄，拍張餐點照片開始第一次分析吧。
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
              <p className="empty-panel">載入中...</p>
            ) : (
              <div className="content-stack">
                <article className="panel-card">
                  <p className="panel-kicker">Snapshot</p>
                  <h3>{selectedHistory.food_summary}</h3>
                  <p>{formatDateLabel(selectedHistory.analyzed_at)}</p>
                </article>

                <div className="metric-grid">
                  <article className="metric-card metric-card-inline">
                    <span>總熱量</span>
                    <div className="metric-card-value">
                      <strong>{selectedHistory.total_kcal}</strong>
                      <small>kcal</small>
                    </div>
                  </article>
                  <article className="metric-card metric-card-inline">
                    <span>蛋白質</span>
                    <div className="metric-card-value">
                      <strong>{selectedHistory.total_protein_g}</strong>
                      <small>g</small>
                    </div>
                  </article>
                  <article className="metric-card metric-card-inline">
                    <span>脂肪</span>
                    <div className="metric-card-value">
                      <strong>{selectedHistory.total_fat_g}</strong>
                      <small>g</small>
                    </div>
                  </article>
                  <article className="metric-card metric-card-inline">
                    <span>碳水</span>
                    <div className="metric-card-value">
                      <strong>{selectedHistory.total_carb_g}</strong>
                      <small>g</small>
                    </div>
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
                              {item.portion_value}{" "}
                              {formatPortionUnit(item.portion_unit)}
                            </p>
                          </div>
                          <span>{item.kcal} kcal</span>
                        </div>
                      ))}
                    </div>
                  </article>

                  <article className="panel-card recommendation-panel">
                    <p className="panel-kicker">Recommendation Snapshot</p>
                    <h3>當次建議快照</h3>
                    {selectedHistory.recommendation.source === "generic" ? (
                      <div className="status-banner is-warning">
                        <strong>通用建議</strong>
                        <span>
                          {selectedHistory.recommendation.guidance_note}
                        </span>
                      </div>
                    ) : null}
                    {historyDisclaimerCopy ? (
                      <InlineDisclaimerNote
                        body={historyDisclaimerCopy.inlineBody}
                      />
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
            {profileError ? (
              <p className="status-banner is-error">{profileError}</p>
            ) : null}
            {profileMessage ? (
              <p className="status-banner is-success">{profileMessage}</p>
            ) : null}

            {profileLoading ? (
              <p className="empty-panel">載入中...</p>
            ) : (
              <>
                <div className="panel-grid profile-layout">
                  <form
                    className="panel-card profile-form"
                    onSubmit={handleProfileSubmit}
                  >
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

                    <label className="profile-select-row">
                      運動習慣
                      <select
                        name="activity_level"
                        value={profileForm.activity_level}
                        onChange={(event) => {
                          const nextValue = event.currentTarget
                            .value as ActivityLevel;
                          setProfileForm((current) => ({
                            ...current,
                            activity_level: nextValue,
                          }));
                        }}
                      >
                        {activityOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label} - {option.hint}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="profile-select-row">
                      目標
                      <select
                        name="goal_type"
                        value={profileForm.goal_type}
                        onChange={(event) => {
                          const nextValue = event.currentTarget
                            .value as GoalType;
                          setProfileForm((current) => ({
                            ...current,
                            goal_type: nextValue,
                          }));
                        }}
                      >
                        {goalOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label} - {option.hint}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="footer-actions">
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
                    <h3>切換主題</h3>
                    <div className="choice-grid two-columns theme-picker">
                      <button
                        type="button"
                        className={
                          themeMode === "female_default"
                            ? "theme-swatch is-active theme-soft"
                            : "theme-swatch theme-soft"
                        }
                        onClick={() => void handleThemeChange("female_default")}
                      >
                        <strong>橘色</strong>
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
                        <strong>藍色</strong>
                      </button>
                    </div>
                  </aside>
                </div>
                <LegalFooter onOpenReview={setActiveLegalReview} />
              </>
            )}
          </section>
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
            <h1>拍張照，知道你吃了什麼</h1>
          </div>
        </header>

        <section className="landing-hero">
          <article className="landing-card landing-card-primary">
            <p className="spotlight-label">HappyMeal</p>
            <h2>用 LINE 登入，開始你的飲食紀錄</h2>
            <p className="landing-copy">
              拍下餐點，AI
              幫你辨識食材與熱量。每一次分析都會存下來，讓你看清楚自己的飲食習慣。
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
            <p className="panel-kicker">功能亮點</p>
            <h3>三步驟完成一次分析</h3>
            <ul className="compact-list">
              <li>拍下餐點，上傳給 AI 辨識。</li>
              <li>確認食材與份量，取得熱量與營養估算。</li>
              <li>查看歷史紀錄，追蹤每日飲食。</li>
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
