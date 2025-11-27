/**
 * Event bus tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EventBus } from '../bus/event-bus.js';
import {
  createFindingEvent,
  createProgressEvent,
  createErrorEvent,
  createCompleteEvent,
} from '../bus/messages.js';
import { FindingSeverity } from '../types/index.js';

describe('EventBus', () => {
  let eventBus: EventBus;

  beforeEach(() => {
    eventBus = new EventBus();
  });

  describe('Event Subscription', () => {
    it('should subscribe to specific event type', () => {
      const handler = vi.fn();
      eventBus.on('progress', handler);

      const event = createProgressEvent('agent-1', 50);
      eventBus.emit(event);

      expect(handler).toHaveBeenCalledWith(event);
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('should unsubscribe from events', () => {
      const handler = vi.fn();
      const unsubscribe = eventBus.on('progress', handler);

      unsubscribe();

      const event = createProgressEvent('agent-1', 50);
      eventBus.emit(event);

      expect(handler).not.toHaveBeenCalled();
    });

    it('should subscribe to event once', () => {
      const handler = vi.fn();
      eventBus.once('progress', handler);

      const event1 = createProgressEvent('agent-1', 50);
      const event2 = createProgressEvent('agent-1', 75);

      eventBus.emit(event1);
      eventBus.emit(event2);

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(event1);
    });

    it('should subscribe to all events with onAny', () => {
      const handler = vi.fn();
      eventBus.onAny(handler);

      const progressEvent = createProgressEvent('agent-1', 50);
      const errorEvent = createErrorEvent('agent-1', 'Test error');

      eventBus.emit(progressEvent);
      eventBus.emit(errorEvent);

      expect(handler).toHaveBeenCalledTimes(2);
      expect(handler).toHaveBeenNthCalledWith(1, progressEvent);
      expect(handler).toHaveBeenNthCalledWith(2, errorEvent);
    });
  });

  describe('Event History', () => {
    it('should track event history', () => {
      const event1 = createProgressEvent('agent-1', 50);
      const event2 = createProgressEvent('agent-2', 75);

      eventBus.emit(event1);
      eventBus.emit(event2);

      const history = eventBus.getAllEvents();
      expect(history).toHaveLength(2);
      expect(history[0]).toEqual(event1);
      expect(history[1]).toEqual(event2);
    });

    it('should get events by correlation ID', () => {
      const correlationId = 'test-correlation-id';
      const event1 = createProgressEvent('agent-1', 50, { correlationId });
      const event2 = createProgressEvent('agent-2', 75);

      eventBus.emit(event1);
      eventBus.emit(event2);

      const events = eventBus.getEventsByCorrelation(correlationId);
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual(event1);
    });

    it('should get events by agent ID', () => {
      const event1 = createProgressEvent('agent-1', 50);
      const event2 = createProgressEvent('agent-2', 75);

      eventBus.emit(event1);
      eventBus.emit(event2);

      const events = eventBus.getEventsByAgent('agent-1');
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual(event1);
    });

    it('should get events by type', () => {
      const progressEvent = createProgressEvent('agent-1', 50);
      const errorEvent = createErrorEvent('agent-1', 'Test error');

      eventBus.emit(progressEvent);
      eventBus.emit(errorEvent);

      const progressEvents = eventBus.getEventsByType('progress');
      expect(progressEvents).toHaveLength(1);
      expect(progressEvents[0]).toEqual(progressEvent);
    });

    it('should get recent events', () => {
      for (let i = 0; i < 10; i++) {
        eventBus.emit(createProgressEvent('agent-1', i * 10));
      }

      const recent = eventBus.getRecentEvents(3);
      expect(recent).toHaveLength(3);
      expect(recent[2].progress).toBe(90);
    });

    it('should clear history', () => {
      eventBus.emit(createProgressEvent('agent-1', 50));
      eventBus.emit(createProgressEvent('agent-2', 75));

      expect(eventBus.getAllEvents()).toHaveLength(2);

      eventBus.clearHistory();

      expect(eventBus.getAllEvents()).toHaveLength(0);
    });

    it('should limit history size', () => {
      const smallBus = new EventBus(10);

      for (let i = 0; i < 20; i++) {
        smallBus.emit(createProgressEvent('agent-1', i));
      }

      const history = smallBus.getAllEvents();
      expect(history).toHaveLength(10);
      expect(history[0].progress).toBe(10); // First 10 were dropped
    });
  });

  describe('Event Messages', () => {
    it('should create finding event', () => {
      const finding = {
        id: 'finding-1',
        severity: FindingSeverity.HIGH,
        category: 'security',
        message: 'Security issue detected',
        filePath: '/path/to/file.ts',
        line: 42,
      };

      const event = createFindingEvent('agent-1', finding);

      expect(event.type).toBe('finding');
      expect(event.agentId).toBe('agent-1');
      expect(event.finding).toEqual(finding);
      expect(event.correlationId).toBeTruthy();
    });

    it('should create progress event', () => {
      const event = createProgressEvent('agent-1', 50, {
        message: 'Processing file',
        currentFile: '/path/to/file.ts',
      });

      expect(event.type).toBe('progress');
      expect(event.agentId).toBe('agent-1');
      expect(event.progress).toBe(50);
      expect(event.message).toBe('Processing file');
      expect(event.currentFile).toBe('/path/to/file.ts');
    });

    it('should create error event', () => {
      const error = new Error('Test error');
      const event = createErrorEvent('agent-1', error, {
        filePath: '/path/to/file.ts',
        fatal: true,
      });

      expect(event.type).toBe('error');
      expect(event.agentId).toBe('agent-1');
      expect(event.error).toBe('Test error');
      expect(event.filePath).toBe('/path/to/file.ts');
      expect(event.fatal).toBe(true);
      expect(event.stack).toBeTruthy();
    });

    it('should create complete event', () => {
      const result = {
        agentId: 'agent-1',
        workItemId: 'work-1',
        filePath: '/path/to/file.ts',
        findings: [],
        duration: 1000,
        success: true,
      };

      const event = createCompleteEvent('agent-1', result, 1000);

      expect(event.type).toBe('complete');
      expect(event.agentId).toBe('agent-1');
      expect(event.result).toEqual(result);
      expect(event.duration).toBe(1000);
    });
  });

  describe('Listener Management', () => {
    it('should count listeners', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      eventBus.on('progress', handler1);
      eventBus.on('progress', handler2);

      expect(eventBus.listenerCount('progress')).toBe(2);
    });

    it('should remove all listeners', () => {
      eventBus.on('progress', vi.fn());
      eventBus.on('error', vi.fn());

      eventBus.removeAllListeners();

      expect(eventBus.listenerCount('progress')).toBe(0);
      expect(eventBus.listenerCount('error')).toBe(0);
    });
  });
});
