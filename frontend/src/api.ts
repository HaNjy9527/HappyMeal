const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type ThemePreference = "female_default" | "male_default";
export type ActivityLevel =
  | "sedentary"
  | "light"
  | "moderate"
  | "active"
  | "very_active";
export type GoalType = "muscle_gain" | "fat_loss";
export type AnalysisStatus = "draft" | "awaiting_confirmation" | "completed";

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
  candidates: AnalysisCandidateItem[];
};

export type AnalysisResultItem = {
  food_name: string;
  normalized_food_name: string;
  portion_value: string;
  portion_unit: string;
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

export type RecommendationSnapshotResponse = {
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
};

export type CandidateDraftItem = {
  food_name: string;
  normalized_food_name: string;
  portion_value: string;
  portion_unit: string;
  confidence_score: string | null;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
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
    let errorMessage = fallbackMessage;

    try {
      const errorPayload = (await response.json()) as { detail?: string };
      errorMessage = errorPayload.detail ?? fallbackMessage;
    } catch {
      errorMessage = fallbackMessage;
    }

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export function getProfile() {
  return requestJson<ProfileResponse>("/profile");
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
