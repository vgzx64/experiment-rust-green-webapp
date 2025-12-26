# CSS Methodology for rust-green Web Dashboard

## Overview
This document defines the CSS architecture and methodology for the rust-green web application. We use a hybrid approach combining **BEM (Block Element Modifier)** for components and **Utility-First** classes for common patterns, all built on a foundation of **CSS Custom Properties** (design tokens).

## 1. Design Tokens (CSS Custom Properties)

### 1.1 Color Tokens
```css
/* Semantic color tokens */
--color-primary: #2e8555;
--color-primary-dark: #1e6b42;
--color-secondary: #4a5568;
--color-danger: #e53e3e;
--color-warning: #d69e2e;
--color-success: #38a169;
--color-info: #3182ce;

/* Neutral colors */
--color-surface: #ffffff;
--color-background: #f8fafc;
--color-border: #e2e8f0;
--color-text: #2d3748;
--color-text-light: #718096;
--color-text-lighter: #a0aec0;
```

### 1.2 Spacing Tokens
```css
/* 4px spacing scale (0.25rem base) */
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.5rem;   /* 24px */
--space-6: 2rem;     /* 32px */
--space-7: 3rem;     /* 48px */
--space-8: 4rem;     /* 64px */
```

### 1.3 Typography Tokens
```css
--font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-family-mono: 'JetBrains Mono', monospace;

--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.125rem;  /* 18px */
--font-size-xl: 1.25rem;   /* 20px */
--font-size-2xl: 1.5rem;   /* 24px */
--font-size-3xl: 2rem;     /* 32px */

--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

### 1.4 Border & Shadow Tokens
```css
--radius-sm: 0.25rem;
--radius-base: 0.5rem;
--radius-lg: 0.75rem;
--radius-full: 9999px;

--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-base: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

## 2. BEM (Block Element Modifier) Naming Convention

### 2.1 Basic Structure
```
.block {}
.block__element {}
.block--modifier {}
```

### 2.2 Examples
```css
/* Block: Header component */
.header {}

/* Element: Logo inside header */
.header__logo {}

/* Modifier: Sticky header variant */
.header--sticky {}

/* Element with modifier: Active nav item */
.header__nav-item--active {}
```

### 2.3 Rules
1. **Blocks** are standalone components (`.header`, `.card`, `.button`)
2. **Elements** are parts of a block (`.header__logo`, `.card__title`)
3. **Modifiers** are variations (`.button--primary`, `.card--featured`)
4. Use **double hyphen** `--` for modifiers
5. Use **double underscore** `__` for elements
6. Never nest elements more than one level deep

## 3. Utility-First Classes

### 3.1 Naming Convention
```
.u-{property}{-side?}-{size}
```

### 3.2 Categories

#### Spacing Utilities
```css
.u-m-2 { margin: var(--space-2); }
.u-mt-4 { margin-top: var(--space-4); }
.u-mx-auto { margin-left: auto; margin-right: auto; }
.u-p-3 { padding: var(--space-3); }
.u-py-5 { padding-top: var(--space-5); padding-bottom: var(--space-5); }
```

#### Typography Utilities
```css
.u-text-center { text-align: center; }
.u-text-primary { color: var(--color-primary); }
.u-font-semibold { font-weight: var(--font-weight-semibold); }
.u-text-sm { font-size: var(--font-size-sm); }
```

#### Display & Layout Utilities
```css
.u-hidden { display: none; }
.u-flex { display: flex; }
.u-flex-col { flex-direction: column; }
.u-items-center { align-items: center; }
.u-justify-between { justify-content: space-between; }
.u-grid { display: grid; }
```

#### Color Utilities
```css
.u-bg-surface { background-color: var(--color-surface); }
.u-bg-primary { background-color: var(--color-primary); }
.u-text-white { color: white; }
.u-border { border: 1px solid var(--color-border); }
```

## 4. File Structure

```
frontend/css/
├── base/           # Foundation styles
│   ├── _reset.css      # CSS resets
│   ├── _typography.css # Base typography
│   └── _global.css     # Global styles
├── tokens/         # Design tokens
│   ├── _colors.css
│   ├── _spacing.css
│   ├── _typography.css
│   ├── _borders.css
│   └── _index.css      # Exports all tokens
├── utilities/      # Utility classes
│   ├── _spacing.css
│   ├── _typography.css
│   ├── _display.css
│   ├── _colors.css
│   └── _index.css      # Exports all utilities
├── components/     # BEM components
│   ├── _header.css
│   ├── _input-section.css
│   ├── _results-section.css
│   ├── _buttons.css
│   ├── _cards.css
│   └── _index.css      # Exports all components
├── layouts/        # Layout-specific styles
│   ├── _grid.css
│   └── _index.css      # Exports layout styles
└── main.css        # Main entry point (imports everything)
```

## 5. Component Architecture

### 5.1 Component Structure
Each component file should follow this pattern:

```css
/* components/_button.css */

/* Block */
.button {
  /* Base styles */
}

/* Elements */
.button__icon {}
.button__label {}

/* Modifiers */
.button--primary {
  /* Primary variant */
}

.button--large {
  /* Large size variant */
}

.button--disabled {
  /* Disabled state */
}

/* State modifiers (often combined with JS) */
.button.is-loading {}
.button.has-error {}
```

### 5.2 Responsive Design
```css
/* Mobile-first approach */
.header {
  padding: var(--space-4);
}

/* Tablet and up */
@media (min-width: 768px) {
  .header {
    padding: var(--space-6);
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .header {
    padding: var(--space-8);
  }
}
```

## 6. Migration Strategy

### 6.1 Phase 1: Foundation
1. Create design tokens
2. Set up file structure
3. Create utility classes

### 6.2 Phase 2: Component Refactoring
1. Convert one component at a time
2. Update HTML class names incrementally
3. Test each component thoroughly

### 6.3 Phase 3: Optimization
1. Remove old CSS classes
2. Optimize file size
3. Document patterns

## 7. Code Quality Rules

### 7.1 Do's
- ✅ Use design tokens for all values
- ✅ Follow BEM naming strictly
- ✅ Use utility classes for common patterns
- ✅ Write mobile-first responsive code
- ✅ Add comments for complex components

### 7.2 Don'ts
- ❌ Use `!important` (except for utilities)
- ❌ Nest CSS more than 3 levels deep
- ❌ Use ID selectors for styling
- ❌ Use inline styles
- ❌ Create overly specific selectors

## 8. Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

## 9. Performance Guidelines

1. **Minimize specificity**: Keep selectors simple
2. **Avoid over-nesting**: Maximum 3 levels deep
3. **Use efficient selectors**: Class selectors are fastest
4. **Critical CSS**: Load essential styles first
5. **Remove unused CSS**: Regular audits

## 10. Testing

### 10.1 Visual Testing
- Check all breakpoints (mobile, tablet, desktop)
- Verify color contrast accessibility
- Test interactive states (hover, focus, active)

### 10.2 Accessibility Testing
- Sufficient color contrast (WCAG AA minimum)
- Keyboard navigation
- Screen reader compatibility

---

## Appendix A: Class Name Conversion Table

| Old Class | New BEM Class | Notes |
|-----------|---------------|-------|
| `.simple-header` | `.header` | Block |
| `.header-content` | `.header__content` | Element |
| `.simple-nav` | `.header__nav` | Element |
| `.nav-item.active` | `.header__nav-item--active` | Modifier |
| `.input-section` | `.input-section` | Block |
| `.code-input` | `.input-section__code-input` | Element |
| `.primary-btn` | `.button--primary` | Modifier on button block |

## Appendix B: Common Utility Patterns

```css
/* Centering */
.u-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Screen reader only */
.u-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Truncate text */
.u-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

---

*Last Updated: December 25, 2025*  
*Version: 1.0.0*
