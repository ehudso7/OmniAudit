import {
  BaseTransformer,
  ReactMemoTransformer,
  UseMemoTransformer,
  RemoveConsoleTransformer,
} from './base-transformer';
import type { Transformer } from '../types/index';

export class TransformerFactory {
  private static readonly TRANSFORMERS = new Map<string, new () => Transformer>([
    ['react-memo-transformer', ReactMemoTransformer],
    ['usememo-transformer', UseMemoTransformer],
    ['remove-console-transformer', RemoveConsoleTransformer],
  ]);

  static createTransformer(name: string): Transformer {
    const TransformerClass = this.TRANSFORMERS.get(name);

    if (!TransformerClass) {
      throw new Error(`Unknown transformer: ${name}`);
    }

    return new TransformerClass();
  }

  static getAvailableTransformers(): string[] {
    return Array.from(this.TRANSFORMERS.keys());
  }

  static registerTransformer(name: string, transformerClass: new () => Transformer): void {
    this.TRANSFORMERS.set(name, transformerClass);
  }
}

export {
  BaseTransformer,
  ReactMemoTransformer,
  UseMemoTransformer,
  RemoveConsoleTransformer,
};
export type { Transformer };
