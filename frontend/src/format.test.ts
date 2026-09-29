import { describe, expect, it } from 'vitest';
describe('WELLSAGE client smoke', () => {
  it('keeps metric units explicit', () => {
    const depth = 1250;
    expect(`${depth.toLocaleString()} m`).toBe('1,250 m');
  });
});
