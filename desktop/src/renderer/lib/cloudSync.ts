import { getApiClient } from './api';

export interface CloudSyncEvent {
  client_event_id: string;
  entity_type: string;
  entity_id: string;
  revision: number;
  payload: Record<string, unknown>;
}

export interface CloudSyncRemoteEvent extends CloudSyncEvent {
  cursor: number;
  payload_digest: string;
  created_at: string;
}

export interface EncryptedOutboxAdapter {
  /** Implement with Electron safe-storage or OS keychain; never browser localStorage. */
  readPending(): Promise<CloudSyncEvent[]>;
  writePending(events: CloudSyncEvent[]): Promise<void>;
  readCursor(): Promise<number>;
  writeCursor(cursor: number): Promise<void>;
}

export type CloudSyncStatus = 'idle' | 'syncing' | 'retrying' | 'blocked';

interface CloudSyncClientOptions {
  organizationId: string;
  outbox: EncryptedOutboxAdapter;
  onRemoteEvents: (events: CloudSyncRemoteEvent[]) => Promise<void>;
  onStatus?: (status: CloudSyncStatus, detail?: string) => void;
  intervalMs?: number;
  token?: string;
}

/**
 * A deterministic client-side scheduler for the encrypted server journal.
 * Financial payloads are retained only in a caller-provided encrypted outbox.
 */
export class CloudSyncClient {
  private readonly intervalMs: number;
  private timer: number | null = null;
  private isSyncing = false;

  constructor(private readonly options: CloudSyncClientOptions) {
    this.intervalMs = Math.max(options.intervalMs ?? 60_000, 5_000);
  }

  start(): void {
    if (this.timer !== null) return;
    void this.syncNow();
    this.timer = window.setInterval(() => void this.syncNow(), this.intervalMs);
  }

  stop(): void {
    if (this.timer !== null) window.clearInterval(this.timer);
    this.timer = null;
  }

  async enqueue(event: CloudSyncEvent): Promise<void> {
    const pending = await this.options.outbox.readPending();
    if (pending.some((candidate) => candidate.client_event_id === event.client_event_id)) return;
    await this.options.outbox.writePending([...pending, event]);
    void this.syncNow();
  }

  async syncNow(): Promise<void> {
    if (this.isSyncing) return;
    this.isSyncing = true;
    this.options.onStatus?.('syncing');
    try {
      const client = await getApiClient();
      const headers = {
        'X-Organization-ID': this.options.organizationId,
        ...(this.options.token ? { 'X-Cloud-Sync-Token': this.options.token } : {}),
      };
      const pending = await this.options.outbox.readPending();
      const unsent: CloudSyncEvent[] = [];

      for (const event of pending) {
        try {
          await client.post('/cloud-sync/push', event, { headers });
        } catch {
          unsent.push(event);
        }
      }
      await this.options.outbox.writePending(unsent);

      const cursor = await this.options.outbox.readCursor();
      const { data } = await client.get<{ events: CloudSyncRemoteEvent[]; next_cursor: number }>('/cloud-sync/pull', {
        params: { after_cursor: cursor },
        headers,
      });
      if (data.events.length) await this.options.onRemoteEvents(data.events);
      await this.options.outbox.writeCursor(data.next_cursor);
      this.options.onStatus?.(unsent.length ? 'retrying' : 'idle', unsent.length ? `${unsent.length} event(s) remain queued` : undefined);
    } catch (error: any) {
      this.options.onStatus?.('retrying', error?.message || 'Cloud Sync is temporarily unavailable');
    } finally {
      this.isSyncing = false;
    }
  }
}
