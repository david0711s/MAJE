import { StyleSheet } from 'react-native';

export const Typography = {
  family: {
    sans:  'Inter',
    mono:  'JetBrainsMono',
  },
  size: {
    xs:   11,
    sm:   13,
    base: 15,
    md:   17,
    lg:   20,
    xl:   24,
    xxl:  30,
    hero: 38,
  },
  weight: {
    regular:  '400' as const,
    medium:   '500' as const,
    semibold: '600' as const,
    bold:     '700' as const,
  },
  lineHeight: {
    tight:  1.2,
    normal: 1.5,
    loose:  1.8,
  },
};

export const TypographyStyles = StyleSheet.create({
  hero:    { fontSize: Typography.size.hero,  fontWeight: Typography.weight.bold,     letterSpacing: -1.5 },
  h1:      { fontSize: Typography.size.xxl,   fontWeight: Typography.weight.bold,     letterSpacing: -0.8 },
  h2:      { fontSize: Typography.size.xl,    fontWeight: Typography.weight.semibold, letterSpacing: -0.5 },
  h3:      { fontSize: Typography.size.lg,    fontWeight: Typography.weight.semibold, letterSpacing: -0.3 },
  body:    { fontSize: Typography.size.base,  fontWeight: Typography.weight.regular,  lineHeight: 22 },
  bodyMd:  { fontSize: Typography.size.md,    fontWeight: Typography.weight.regular,  lineHeight: 26 },
  caption: { fontSize: Typography.size.sm,    fontWeight: Typography.weight.regular,  lineHeight: 18 },
  tiny:    { fontSize: Typography.size.xs,    fontWeight: Typography.weight.medium,   letterSpacing: 0.3 },
  label:   { fontSize: Typography.size.sm,    fontWeight: Typography.weight.semibold, letterSpacing: 0.2 },
  mono:    { fontSize: Typography.size.sm,    fontWeight: Typography.weight.regular,  letterSpacing: 0.1 },
});
