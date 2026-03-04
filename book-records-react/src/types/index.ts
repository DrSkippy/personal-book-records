// src/types/index.ts

export interface Book {
  BookId: number;
  Title: string;
  Author: string;
  CopyrightDate: string | null;
  IsbnNumber: string | null;
  IsbnNumber13: string | null;
  PublisherName: string | null;
  CoverType: 'Hard' | 'Soft' | 'Digital' | null;
  Pages: number | null;
  BookNote: string | null;
  Recycled: 0 | 1;
  Location: string;
  LastUpdate: string;
  ReadDate?: string | null;
}

export interface ReadRecord {
  BookId: number;
  DateRead: string;
  ReadNote: string | null;
  LastUpdate: string;
}

export interface Tag {
  TagId: number;
  Label: string;
}

export interface Image {
  ImageId: number;
  BookId: number;
  Name: string | null;
  Url: string | null;
  ImageType: string;
}

export interface ReadingEstimate {
  RecordId: number;
  BookId: number;
  StartDate: string;
  LastReadablePage: number;
  EstimateDate: string | null;
  EstimatedFinishDate: string | null;
}

export interface DailyPageRecord {
  RecordId: number;
  RecordDate: string;
  Page: number;
  LastUpdate: string;
}

export interface CompleteRecord {
  book: StandardResponse;
  reads: StandardResponse;
  tags: StandardResponse;
  img: StandardResponse;
}

export interface StandardResponse {
  data: Array<Array<string | number | null>>;
  header: string[];
  error: string[];
}

export interface YearlySummary {
  year: number;
  'books read': number;
  'pages read': number;
}

export interface TagCount {
  tag: string;
  count: number;
}

export type Location =
  | 'Main Collection'
  | 'Bedroom'
  | 'Storage'
  | 'Oversized'
  | 'Pets'
  | 'Woodwork'
  | 'Reference'
  | 'Birding';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolCallId?: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
  toolResult?: unknown;
}
