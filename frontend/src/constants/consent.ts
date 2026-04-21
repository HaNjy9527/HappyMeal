export type ConsentContentSection = {
  id: "privacy" | "non-medical";
  kicker: string;
  title: string;
  summary: string;
  checkboxLabel: string;
  paragraphs: string[];
};

export const consentUiCopy = {
  disclaimerCard: {
    kicker: "Non-medical reminder",
    title: "本服務非醫療用途",
    body: "此建議僅供日常健康管理參考，不構成醫療診斷、治療或處方。若你有健康疑慮，請諮詢合格醫療專業人士。",
  },
  spotlight: {
    title: "Consent Intro",
    copy: "先完成隱私政策與非醫療用途同意，才能開始新的分析與建議流程。",
  },
  introCard: {
    kicker: "Privacy & disclosure",
    title: "開始分析前，請先完成兩項必要同意",
    description:
      "你可以先看摘要，再依需要展開完整文案。完成兩項勾選後，才能開始新的分析與建議流程。",
  },
  helper: {
    incomplete: "請先勾選兩項同意後，才能繼續。",
    complete: "已符合送出條件，送出後會回到分析主流程。",
  },
  footer: {
    kicker: "Legal & consent",
    description:
      "完成同意後，如需重新查看隱私政策與非醫療用途聲明，可從這裡前往頁尾。",
    action: "查看隱私與聲明",
  },
  review: {
    kicker: "Privacy & Consent Review",
    title: "隱私與聲明",
    description: "以下內容提供你於一般使用期間隨時回看，不影響目前主流程操作。",
  },
  action: {
    submit: "同意並繼續",
    submitting: "送出中...",
    goToConsent: "前往 Consent",
  },
  message: {
    checkboxRequired: "請先勾選兩項同意後，再繼續。",
    updated: "同意已更新，現在可以開始分析與查看建議。",
    saveFailed: "Consent 儲存失敗",
    analysisRequired: "開始分析前，請先完成隱私政策與非醫療用途同意。",
    flowRequired: "完成兩項同意後，才能開始新的分析與建議流程。",
    confirmRequired: "完成候選確認前，請先完成隱私政策與非醫療用途同意。",
    lockedSummary: "尚未完成必要同意，請先前往 Consent。",
    unlockedSummary: "已完成必要同意，可開始新的分析。",
    profileReady: "目前已可開始新的分析與建議流程。",
    profilePending: "開始分析前，請先完成隱私政策與非醫療用途同意。",
  },
  profileStatus: {
    label: "Consent 狀態",
    completed: "已完成",
    pending: "待補齊",
  },
};

export const consentSections: ConsentContentSection[] = [
  {
    id: "privacy",
    kicker: "Privacy Policy",
    title: "隱私政策說明",
    summary:
      "我們會使用你的基本身體資料、目標設定與食物照片來完成分析，原始照片僅供本次分析暫存，完成後不長期保存。",
    checkboxLabel: "我已閱讀並同意目前版本的隱私政策",
    paragraphs: [
      "為了提供飲食分析、營養估算與個人化建議，HappyMeal 會處理你填寫的年齡、身高、體重、活動量、目標設定，以及你上傳的食物照片與分析結果摘要。",
      "原始食物照片僅用於本次分析流程的暫存處理，分析完成後不作長期保存。歷史紀錄中保存的是分析摘要、營養結果與建議快照，不包含原始照片。",
      "你的資料僅用於提供本服務所需的功能與體驗優化，不會因前端流程需要而把第三方金鑰或敏感設定暴露在瀏覽器端。",
    ],
  },
  {
    id: "non-medical",
    kicker: "Non-medical Disclosure",
    title: "非醫療用途聲明",
    summary:
      "本服務提供的是一般健康管理與 wellness guidance 參考，不構成醫療診斷、治療、處方或專業醫療建議。",
    checkboxLabel: "我已閱讀並同意非醫療用途聲明",
    paragraphs: [
      "HappyMeal 提供的熱量、營養與運動建議，屬於一般健康管理與 wellness guidance 參考，目的在於協助你理解單次飲食與活動安排。",
      "所有營養結果與建議都屬於估算資訊，不能取代醫師、營養師或其他合格醫療專業人員的判斷，也不應被解讀為診斷、治療、處方或疾病管理方案。",
      "如果你有慢性病、特殊飲食限制、孕期需求或任何健康疑慮，請優先諮詢合格醫療專業人員，再決定是否依據本服務的資訊調整飲食或運動安排。",
    ],
  },
];
