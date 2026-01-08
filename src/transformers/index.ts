import type { Transformer } from '../types/index';
import {
  BaseTransformer,
  ReactMemoTransformer,
  RemoveConsoleTransformer,
  UseMemoTransformer,
} from './base-transformer';

export class TransformerFactory {
  private static readonly TRANSFORMERS = new Map<string, new () => Transformer>([
    ['react-memo-transformer', ReactMemoTransformer],
    ['usememo-transformer', UseMemoTransformer],
    ['remove-console-transformer', RemoveConsoleTransformer],
  ]);

  static createTransformer(name: string): Transformer {
    const TransformerClass = TransformerFactory.TRANSFORMERS.get(name);

    if (!TransformerClass) {
      throw new Error(`Unknown transformer: ${name}`);
    }

    return new TransformerClass();
  }

  static getAvailableTransformers(): string[] {
    return Array.from(TransformerFactory.TRANSFORMERS.keys());
  }

  static registerTransformer(name: string, transformerClass: new () => Transformer): void {
    TransformerFactory.TRANSFORMERS.set(name, transformerClass);
  }
}

export { BaseTransformer, ReactMemoTransformer, UseMemoTransformer, RemoveConsoleTransformer };
export type { Transformer };
