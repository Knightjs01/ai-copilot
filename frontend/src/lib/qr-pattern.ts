// A deterministic, QR-code-shaped pixel grid seeded from the Passport's real Callsign — purely
// decorative. There is no public single-candidate URL anywhere in this product for a real QR
// code to resolve to, so this never claims to be scannable; it exists only to make the final
// Passport credential visual feel like a finished, premium artifact. Never call this "scan me"
// or imply it encodes anything.
const GRID_SIZE = 21;
const FINDER_SIZE = 7;

function hashSeed(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return hash >>> 0;
}

function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function isInFinderZone(row: number, col: number): boolean {
  const zones: Array<[number, number]> = [
    [0, 0],
    [0, GRID_SIZE - FINDER_SIZE],
    [GRID_SIZE - FINDER_SIZE, 0],
  ];
  return zones.some(
    ([zr, zc]) => row >= zr && row < zr + FINDER_SIZE && col >= zc && col < zc + FINDER_SIZE
  );
}

function finderPatternValue(row: number, col: number): boolean {
  // A classic QR finder square: solid border, empty ring, solid 3x3 center.
  const isBorder = row === 0 || row === FINDER_SIZE - 1 || col === 0 || col === FINDER_SIZE - 1;
  const isCenter = row >= 2 && row <= 4 && col >= 2 && col <= 4;
  return isBorder || isCenter;
}

export function generateQrPattern(seed: string): boolean[][] {
  const random = mulberry32(hashSeed(seed));
  const grid: boolean[][] = [];
  for (let row = 0; row < GRID_SIZE; row++) {
    const rowCells: boolean[] = [];
    for (let col = 0; col < GRID_SIZE; col++) {
      if (isInFinderZone(row, col)) {
        const zoneRow = row < FINDER_SIZE ? row : row - (GRID_SIZE - FINDER_SIZE);
        const zoneCol = col < FINDER_SIZE ? col : col - (GRID_SIZE - FINDER_SIZE);
        rowCells.push(finderPatternValue(zoneRow, zoneCol));
      } else {
        rowCells.push(random() > 0.55);
      }
    }
    grid.push(rowCells);
  }
  return grid;
}
