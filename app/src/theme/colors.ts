/**
 * MAJE App – Color Palette (Dark Theme)
 * Inspired by Linear / Raycast / Arc Browser aesthetics
 */

export const Colors = {
  // ── Backgrounds ────────────────────────────────────────────────
  bg: {
    primary:   '#0C0C0F',   // Almost black
    secondary: '#13131A',   // Cards, panels
    tertiary:  '#1A1A26',   // Elevated surfaces
    elevated:  '#1F1F2E',   // Modals, popovers
    glass:     'rgba(255,255,255,0.04)',
    base:      '#0C0C0F',   // Alias for screen background
    surface:   '#13131A',   // Alias for card surface
    overlay:   '#1A1A26',   // Alias for interactive elements
  },

  // ── Accent / Brand ─────────────────────────────────────────────
  accent: {
    primary:      '#7C6EFA',   // Violet – main brand
    secondary:    '#9D8FF7',   // Lighter violet
    glow:         'rgba(124,110,250,0.25)',
    muted:        'rgba(124,110,250,0.12)',
    primaryMuted: 'rgba(124,110,250,0.15)',
    error:        '#FF6B7A',
    success:      '#4ADE80',
    warning:      '#FBBF24',
    info:         '#38BDF8',
  },

  // ── Text ───────────────────────────────────────────────────────
  text: {
    primary:   '#F0F0FF',   // Near white with slight blue tint
    secondary: '#8B8BA8',   // Muted text
    tertiary:  '#505068',   // Very muted
    muted:     '#8B8BA8',   // Alias for secondary
    accent:    '#7C6EFA',
    error:     '#FF6B7A',
    success:   '#4ADE80',
    warning:   '#FBBF24',
  },

  // ── Status / Semantic ──────────────────────────────────────────
  status: {
    running:   '#4ADE80',
    stopped:   '#FF6B7A',
    pending:   '#FBBF24',
    completed: '#34D399',
    failed:    '#FF6B7A',
    paused:    '#60A5FA',
  },

  // ── Mode Colors ────────────────────────────────────────────────
  mode: {
    chat:      '#60A5FA',   // Blue
    agent:     '#7C6EFA',   // Violet
    autonomy:  '#F472B6',   // Pink (experimental)
  },

  // ── Borders ────────────────────────────────────────────────────
  border: {
    subtle:    'rgba(255,255,255,0.06)',
    default:   'rgba(255,255,255,0.10)',
    focus:     'rgba(124,110,250,0.50)',
    strong:    'rgba(255,255,255,0.15)',
  },

  // ── Provider Badges ────────────────────────────────────────────
  provider: {
    gemini:    '#4285F4',
    groq:      '#F97316',
    deepseek:  '#10B981',
    openai:    '#10A37F',
    anthropic: '#D97706',
    default:   '#6B7280',
  },
} as const;

export type ColorKey = typeof Colors;
