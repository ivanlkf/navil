import { useCallback, useSyncExternalStore } from 'react'

/**
 * Module-level in-memory store — survives component unmount/remount
 * but clears on full page reload (no sessionStorage).
 */
const memStore = new Map<string, string>()

/** Per-key listeners for useSyncExternalStore reactivity. */
const listeners = new Map<string, Set<() => void>>()

/**
 * Parse cache — ensures useSyncExternalStore sees the same object
 * reference for the same raw string, preventing infinite re-renders.
 */
const parsedCache = new Map<string, { raw: string; parsed: unknown }>()

function storeGet(key: string): string | null {
  return memStore.get(key) ?? null
}

function storeSet(key: string, value: string): void {
  memStore.set(key, value)
  notify(key)
}

function storeRemove(key: string): void {
  memStore.delete(key)
  parsedCache.delete(key)
  notify(key)
}

/** Notify all subscribers of a key that the value changed. */
function notify(key: string): void {
  listeners.get(key)?.forEach(cb => cb())
}

/** Subscribe to changes for a key. Returns unsubscribe function. */
function subscribeToKey(key: string, callback: () => void): () => void {
  if (!listeners.has(key)) listeners.set(key, new Set())
  listeners.get(key)!.add(callback)
  return () => { listeners.get(key)?.delete(callback) }
}

/**
 * Read and parse the stored value, returning a **stable object reference**
 * (same ref if the raw string hasn't changed) so useSyncExternalStore
 * won't infinite-loop.
 */
function readSnapshot<T>(key: string, initial: T): T {
  const raw = storeGet(key)
  if (!raw) return initial

  const cached = parsedCache.get(key)
  if (cached && cached.raw === raw) return cached.parsed as T

  try {
    const parsed = JSON.parse(raw) as T
    parsedCache.set(key, { raw, parsed })
    return parsed
  } catch {
    return initial
  }
}

/**
 * useState-like hook that persists across React Router navigation.
 *
 * Uses an in-memory Map as the primary store (with optional sessionStorage
 * enhancement).  Backed by `useSyncExternalStore` so that writes from
 * **any** source — including old unmounted-component async callbacks —
 * automatically trigger a re-render in whichever component is currently
 * mounted with the same key.
 *
 * Keys are prefixed with `navil_` to avoid collisions.
 */
export default function useSessionState<T>(
  key: string,
  initial: T,
): [T, (v: T | ((prev: T) => T)) => void] {
  const fullKey = `navil_${key}`

  const subscribe = useCallback(
    (cb: () => void) => subscribeToKey(fullKey, cb),
    [fullKey],
  )

  const getSnapshot = useCallback(
    () => readSnapshot(fullKey, initial),
    [fullKey, initial],
  )

  const value = useSyncExternalStore(subscribe, getSnapshot)

  const set = useCallback(
    (v: T | ((prev: T) => T)) => {
      const prev = readSnapshot(fullKey, initial)
      const next = typeof v === 'function' ? (v as (p: T) => T)(prev) : v
      if (next === null || next === undefined || next === '') {
        storeRemove(fullKey)
      } else {
        storeSet(fullKey, JSON.stringify(next))
      }
      // storeSet / storeRemove already call notify(),
      // which triggers useSyncExternalStore re-renders.
    },
    [fullKey, initial],
  )

  return [value, set]
}
