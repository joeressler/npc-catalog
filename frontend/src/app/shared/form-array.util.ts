import { FormArray } from '@angular/forms';

/**
 * Swap a FormArray item with its neighbour in the given direction.
 * `-1` moves the item up (towards index 0), `1` moves it down.
 * No-ops when the move would fall outside the array bounds.
 */
export function moveFormArrayItem(array: FormArray, index: number, direction: -1 | 1): void {
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= array.length) {
    return;
  }
  const current = array.at(index);
  array.setControl(index, array.at(targetIndex));
  array.setControl(targetIndex, current);
}

/** Add the id to the set if absent, otherwise remove it. */
export function toggleIdInSet(set: Set<number>, id: number): void {
  if (set.has(id)) {
    set.delete(id);
  } else {
    set.add(id);
  }
}
