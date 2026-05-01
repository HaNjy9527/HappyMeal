const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type ApiErrorDetail = {
  code?: string;
  message?: string;
};

export class ApiError extends Error {
  code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

export type ThemePreference = "female_default" | "male_default";
export type ActivityLevel =
  | "sedentary"
  | "light"
  | "moderate"
  | "active"
  | "very_active";
export type GoalType = "muscle_gain" | "fat_loss";
export type AnalysisStatus = "draft" | "awaiting_confirmation" | "completed";
export type RecognitionStatus = "success" | "partial" | "complete_failure";

export type ConsentStatus = {
  has_privacy_policy: boolean;
  has_non_medical_disclosure: boolean;
  can_start_analysis: boolean;
  can_view_guidance: boolean;
};

export type RequiredPolicyVersions = {
  privacy_policy: string;
  non_medical_disclosure: string;
};

export type ProfileResponse = {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  theme_preference: ThemePreference;
  profile: {
    age: number | null;
    height_cm: number | null;
    weight_kg: string | null;
    activity_level: ActivityLevel | null;
    goal_type: GoalType | null;
    goal_weight_kg: string | null;
    updated_at: string | null;
  };
};

export type AuthMeResponse = {
  id: string;
  display_name: string;
  avatar_url: string | null;
  theme_preference: ThemePreference;
  consent_status: ConsentStatus;
  required_policy_versions: RequiredPolicyVersions;
};

export type DisclaimerResponse = {
  title: string;
  body: string;
  policy_version: string;
  consent_type: "privacy_policy" | "non_medical_disclosure";
};

export type ProfileUpdateRequest = {
  age: number;
  height_cm: number;
  weight_kg: number;
  activity_level: ActivityLevel;
  goal_type: GoalType;
  goal_weight_kg: number | null;
};

export type AnalysisCandidateItem = {
  food_name: string;
  normalized_food_name: string;
  confidence_score: string;
  portion_default: string;
  portion_unit: string;
};

export type AnalysisCandidateResponse = {
  analysis_id: string;
  status: AnalysisStatus;
  recognition_status: RecognitionStatus;
  candidates: AnalysisCandidateItem[];
  manual_review_required: boolean;
  fallback_reason: string | null;
  message: string | null;
};

export type AnalysisReestimateResponse = {
  analysis_id: string;
  recognition_status: RecognitionStatus;
  message: string | null;
  fallback_reason: string | null;
  candidates: AnalysisCandidateItem[];
};

export type AnalysisResultItem = {
  food_name: string;
  normalized_food_name: string;
  portion_value: string;
  portion_unit: string;
  source_portion_unit: string | null;
  canonical_food_name: string | null;
  nutrition_source: string | null;
  is_estimated: boolean;
  resolved_weight_g: string | null;
  weight_estimation_method: string | null;
  confidence_score: string | null;
  kcal: string;
  protein_g: string;
  fat_g: string;
  carb_g: string;
};

export type RecommendedExerciseItem = {
  exercise_id: string;
  name: string;
  category: string;
  duration_minutes: number;
  burn_estimate_kcal: string;
};

export type RecommendationSource = "personalized" | "generic";

export type RecommendationSnapshotResponse = {
  source: RecommendationSource;
  guidance_note: string | null;
  target_calories_kcal: string;
  target_protein_g: string;
  target_fat_g: string;
  target_carb_g: string;
  recommended_exercises: RecommendedExerciseItem[];
};

export type AnalysisResultResponse = {
  analysis_id: string;
  analyzed_at: string;
  status: AnalysisStatus;
  total_kcal: string;
  total_protein_g: string;
  total_fat_g: string;
  total_carb_g: string;
  items: AnalysisResultItem[];
  recommendation: RecommendationSnapshotResponse;
  disclaimer: DisclaimerResponse;
};

export type AnalysisHistoryListItem = {
  analysis_id: string;
  analyzed_at: string;
  total_kcal: string;
  food_summary: string;
  recommendation_summary: string;
};

export type AnalysisHistoryListResponse = {
  items: AnalysisHistoryListItem[];
};

export type AnalysisHistoryDetailResponse = {
  analysis_id: string;
  analyzed_at: string;
  status: AnalysisStatus;
  food_summary: string;
  total_kcal: string;
  total_protein_g: string;
  total_fat_g: string;
  total_carb_g: string;
  items: AnalysisResultItem[];
  recommendation: RecommendationSnapshotResponse;
  disclaimer: DisclaimerResponse;
};

function buildApiError(
  detail: string | ApiErrorDetail | undefined,
  fallbackMessage: string,
) {
  if (typeof detail === "string") {
    return new ApiError(detail);
  }

  if (detail && typeof detail === "object") {
    return new ApiError(detail.message ?? fallbackMessage, detail.code);
  }

  return new ApiError(fallbackMessage);
}

export type CandidateDraftItem = {
  id: string;
  is_manual: boolean;
  food_name: string;
  normalized_food_name: string;
  portion_value: string;
  portion_unit: string;
  confidence_score: string | null;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}`;

    try {
      const errorPayload = (await response.json()) as {
        detail?: string | ApiErrorDetail;
      };
      throw buildApiError(errorPayload.detail, fallbackMessage);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(fallbackMessage);
    }
  }

  return (await response.json()) as T;
}

export function getProfile() {
  return requestJson<ProfileResponse>("/profile");
}

export async function getMe() {
  const response = await fetch(`${apiBaseUrl}/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}`;

    try {
      const errorPayload = (await response.json()) as {
        detail?: string | ApiErrorDetail;
      };
      throw buildApiError(errorPayload.detail, fallbackMessage);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(fallbackMessage);
    }
  }

  return (await response.json()) as AuthMeResponse;
}

export function createConsent(
  consentType: "privacy_policy" | "non_medical_disclosure",
  policyVersion: string,
) {
  return requestJson<{
    id: string;
    consent_type: string;
    policy_version: string;
    accepted_at: string;
  }>("/consents", {
    method: "POST",
    body: JSON.stringify({
      consent_type: consentType,
      policy_version: policyVersion,
    }),
  });
}

export function logout() {
  return requestJson<{ message: string }>("/auth/logout", {
    method: "POST",
  });
}

export function exchangeAuthToken(token: string) {
  return requestJson<AuthMeResponse>("/auth/exchange-token", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function updateProfile(payload: ProfileUpdateRequest) {
  return requestJson<ProfileResponse>("/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function updateThemePreference(themePreference: ThemePreference) {
  return requestJson<ProfileResponse>("/profile/theme", {
    method: "PUT",
    body: JSON.stringify({ theme_preference: themePreference }),
  });
}

export function createAnalysisDraft() {
  return requestJson<{
    id: string;
    analyzed_at: string;
    status: AnalysisStatus;
  }>("/analyses", {
    method: "POST",
  });
}

export function uploadAnalysisImage(analysisId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<AnalysisCandidateResponse>(
    `/analyses/${analysisId}/image`,
    {
      method: "POST",
      body: formData,
    },
  );
}

export function confirmAnalysis(
  analysisId: string,
  items: CandidateDraftItem[],
) {
  return requestJson<AnalysisResultResponse>(
    `/analyses/${analysisId}/confirm`,
    {
      method: "POST",
      body: JSON.stringify({
        items: items.map((item) => ({
          food_name: item.food_name,
          normalized_food_name: item.normalized_food_name,
          portion_value: item.portion_value,
          portion_unit: item.portion_unit,
          confidence_score: item.confidence_score,
        })),
      }),
    },
  );
}

export function reestimateAnalysis(
  analysisId: string,
  items: CandidateDraftItem[],
  userInstruction: string,
) {
  return requestJson<AnalysisReestimateResponse>(
    `/analyses/${analysisId}/re-estimate`,
    {
      method: "POST",
      body: JSON.stringify({
        items: items.map((item) => ({
          food_name: item.food_name,
          normalized_food_name: item.normalized_food_name,
          portion_value: item.portion_value,
          portion_unit: item.portion_unit,
          confidence_score: item.confidence_score,
          is_user_edited: true,
        })),
        user_instruction: userInstruction.trim() || null,
      }),
    },
  );
}

export function getAnalysisHistory() {
  return requestJson<AnalysisHistoryListResponse>("/analyses");
}

export function getAnalysisDetail(analysisId: string) {
  return requestJson<AnalysisHistoryDetailResponse>(`/analyses/${analysisId}`);
}

export function createMockImageFile(kind: "salad" | "rice" | "salmon") {
  const fileMap = {
    salad: new File(["fake-jpeg-data"], "salad-lunch.jpg", {
      type: "image/jpeg",
    }),
    rice: new File(["fake-png-data"], "rice-bowl.png", { type: "image/png" }),
    salmon: new File(["fake-jpeg-data"], "salmon-plate.jpg", {
      type: "image/jpeg",
    }),
  } satisfies Record<string, File>;

  return fileMap[kind];
}

export { apiBaseUrl };
