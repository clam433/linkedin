export type ScrapedRow = {
  name: string;
  role: string;
  location: string;
};

export type CollectResponse = {
  count: number;
  results: ScrapedRow[];
};

export type ApiError = {
  error: string;
  message: string;
};