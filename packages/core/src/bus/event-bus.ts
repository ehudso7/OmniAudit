/**
 * Event bus for cross-agent communication
 * @module @omniaudit/core/bus/event-bus
 */

import EventEmitter from 'eventemitter3';
import type { BusEvent, EventType, EventHandler } from './types.js';

/**
 * Type-safe event bus for orchestrator and agent communication
 *
 * Features:
 * - Correlation ID tracking for tracing related events
 * - Type-safe event emission and subscription
 * - Wildcard listeners for all events
 * - Event history for debugging
 *
 * @example
 * ```typescript
 * const bus = new EventBus();
 *
 * // Listen for specific event type
 * bus.on('finding', (event) => {
 *   console.log('Finding:', event.finding);
 * });
 *
 * // Listen for all events
 * bus.onAny((event) => {
 *   console.log('Event:', event.type);
 * });
 *
 * // Emit event
 * bus.emit(createFindingEvent('agent-1', finding));
 * ```
 */
export class EventBus {
  private emitter: EventEmitter;
  private eventHistory: BusEvent[] = [];
  private readonly maxHistorySize: number;

  /**
   * Create a new event bus
   * @param maxHistorySize Maximum number of events to keep in history
   */
  constructor(maxHistorySize = 1000) {
    this.emitter = new EventEmitter();
    this.maxHistorySize = maxHistorySize;
  }

  /**
   * Subscribe to events of a specific type
   * @param eventType Type of event to listen for
   * @param handler Function to handle the event
   * @returns Unsubscribe function
   */
  on<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<BusEvent, { type: T }>>,
  ): () => void {
    this.emitter.on(eventType, handler);
    return () => this.off(eventType, handler);
  }

  /**
   * Subscribe to events of a specific type (one-time)
   * @param eventType Type of event to listen for
   * @param handler Function to handle the event
   * @returns Unsubscribe function
   */
  once<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<BusEvent, { type: T }>>,
  ): () => void {
    this.emitter.once(eventType, handler);
    return () => this.off(eventType, handler);
  }

  /**
   * Unsubscribe from events
   * @param eventType Type of event to stop listening for
   * @param handler Handler function to remove
   */
  off<T extends EventType>(
    eventType: T,
    handler: EventHandler<Extract<BusEvent, { type: T }>>,
  ): void {
    this.emitter.off(eventType, handler);
  }

  /**
   * Subscribe to all events (wildcard listener)
   * @param handler Function to handle any event
   * @returns Unsubscribe function
   */
  onAny(handler: EventHandler<BusEvent>): () => void {
    const listener = (event: BusEvent) => handler(event);

    // Subscribe to all known event types
    const eventTypes: EventType[] = [
      'finding',
      'progress',
      'error',
      'complete',
      'state_change',
      'checkpoint',
      'memory_warning',
    ];

    for (const type of eventTypes) {
      this.emitter.on(type, listener);
    }

    return () => {
      for (const type of eventTypes) {
        this.emitter.off(type, listener);
      }
    };
  }

  /**
   * Emit an event to all subscribers
   * @param event Event to emit
   */
  emit(event: BusEvent): void {
    // Add to history
    this.addToHistory(event);

    // Emit to listeners
    this.emitter.emit(event.type, event);
  }

  /**
   * Get all events with a specific correlation ID
   * @param correlationId Correlation ID to search for
   * @returns Array of events with matching correlation ID
   */
  getEventsByCorrelation(correlationId: string): BusEvent[] {
    return this.eventHistory.filter(
      (event) => 'correlationId' in event && event.correlationId === correlationId,
    );
  }

  /**
   * Get all events from a specific agent
   * @param agentId Agent ID to search for
   * @returns Array of events from the agent
   */
  getEventsByAgent(agentId: string): BusEvent[] {
    return this.eventHistory.filter(
      (event) => 'agentId' in event && event.agentId === agentId,
    );
  }

  /**
   * Get all events of a specific type
   * @param eventType Event type to search for
   * @returns Array of events of the specified type
   */
  getEventsByType<T extends EventType>(
    eventType: T,
  ): Array<Extract<BusEvent, { type: T }>> {
    return this.eventHistory.filter(
      (event) => event.type === eventType,
    ) as Array<Extract<BusEvent, { type: T }>>;
  }

  /**
   * Get recent events
   * @param count Number of events to retrieve
   * @returns Array of recent events
   */
  getRecentEvents(count: number): BusEvent[] {
    return this.eventHistory.slice(-count);
  }

  /**
   * Get all events in history
   * @returns Array of all events
   */
  getAllEvents(): BusEvent[] {
    return [...this.eventHistory];
  }

  /**
   * Clear event history
   */
  clearHistory(): void {
    this.eventHistory = [];
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    this.emitter.removeAllListeners();
  }

  /**
   * Get number of listeners for an event type
   * @param eventType Event type to check
   * @returns Number of listeners
   */
  listenerCount(eventType: EventType): number {
    return this.emitter.listenerCount(eventType);
  }

  /**
   * Add event to history with size limit
   * @param event Event to add
   */
  private addToHistory(event: BusEvent): void {
    this.eventHistory.push(event);

    // Trim history if it exceeds max size
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory = this.eventHistory.slice(-this.maxHistorySize);
    }
  }
}
