// Hợp đồng dữ liệu của API (docs/design/API_Design.md mục 3.4). Trường camelCase.

export type DocStatus = "processing" | "ready" | "error";

export interface ApiDocument {
  id: string;
  name: string;
  sizeBytes: number;
  uploadedAt: string;
  status: DocStatus;
  pageCount: number | null;
  errorCode: string | null;
}

export interface AppConfig {
  qaEnabled: boolean;
  maxFileSizeBytes: number;
  maxFiles: number;
  maxQuestionLength: number;
  maxDocumentsPerQuestion: number;
  acceptedTypes: string[];
  noticeVersion: string | null;
  noticeAccepted: boolean;
}

export interface DataNotice {
  version: string;
  content: string;
  accepted: boolean;
}

export interface ApiCitation {
  id: string;
  documentId: string | null;
  documentName: string | null;
  page: number;
  snippet?: string | null;
  valid: boolean;
}

export interface Problem {
  type?: string;
  title: string;
  status: number;
  code: string;
  detail?: string;
  retryable?: boolean;
  requestId?: string | null;
}

export interface LoginResult {
  accessToken: string;
  expiresIn: number;
  subject: string;
  roles: string[];
}

export interface AskBody {
  question: string;
  documentIds: string[];
  clientMessageId: string;
}

export interface TelemetryWire {
  name: string;
  ts: string;
  sessionId: string;
  appVersion: string;
  props: Record<string, string | number | boolean>;
}

export interface MetricLine {
  id: string;
  label: string;
  value: number | null;
  unit: string;
  target: number;
  comparison: ">=" | "<=";
  status: "met" | "not_met" | "unknown";
  sample: number;
  note: string;
}

export interface MvpReport {
  generatedAt: string;
  conclusive: boolean;
  reasons: string[];
  inputs: { sessions: number; users: number; tasks: number; answers: number };
  metrics: MetricLine[];
  errorRates: { step: string; event: string; failed: number; total: number; rate: number | null }[];
  funnel: { event: string; sessions: number }[];
}

export type MessageStatus =
  "sending" | "streaming" | "complete" | "interrupted" | "failed" | "stopped";

export interface ChatMessage {
  key: string; // khóa phía client
  role: "user" | "ai";
  text: string;
  status: MessageStatus;
  serverId?: string;
  question?: string; // với tin nhắn AI: câu hỏi tương ứng (để thử lại)
  clientMessageId?: string;
  citations: ApiCitation[];
  grounded?: boolean;
  feedback?: "up" | "down" | null;
  errorCode?: string;
  errorText?: string; // thông báo đã làm sạch để hiển thị khi failed/interrupted
  startedAt?: number;
}
