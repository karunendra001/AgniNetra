// Single source of truth for fire-type emoji + colors.
// Used by map markers, table badges, alerts, and filter pills.

export const FIRE_TYPES = {
  'Vegetation Fire': {
    emoji: '🔥',
    color: '#ff4757',
    label: 'Vegetation Fire',
  },
  'Industrial Heat Source': {
    emoji: '🏭',
    color: '#ff9f43',
    label: 'Industrial Heat Source',
  },
  'Persistent Thermal Anomaly': {
    emoji: '♨️',
    color: '#a55eea',
    label: 'Persistent Thermal Anomaly',
  },
  'Unclassified': {
    emoji: '❓',
    color: '#778ca3',
    label: 'Unclassified',
  },
};

export const CLASSIFICATIONS = Object.keys(FIRE_TYPES);

export function typeInfo(classification) {
  return FIRE_TYPES[classification] || FIRE_TYPES['Unclassified'];
}

/** "🔥 Vegetation Fire" */
export function emojiLabel(classification) {
  const t = typeInfo(classification);
  return `${t.emoji} ${t.label}`;
}

/** "🔥" or "❓" */
export function emojiOf(classification) {
  return typeInfo(classification).emoji;
}

/** "#ff4757" (falls back to unclassified color) */
export function colorOf(classification) {
  return typeInfo(classification).color;
}
