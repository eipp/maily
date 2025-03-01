# Maily ESLint Configuration

A shared ESLint configuration package for all Maily applications and packages, ensuring consistent code style and quality across the entire project.

## Features

- Extends proven configurations from Next.js, Turbo, and Prettier
- Enforces consistent coding practices across all Maily codebases
- Reduces the need for per-project ESLint configuration
- Works with TypeScript and React projects
- Integrated with the Maily development workflow

## Installation

Since this package is used within the Maily monorepo, it's typically available through workspace dependencies. However, you can also install it directly:

```bash
# Within the Maily monorepo
pnpm add eslint-config-maily --workspace

# Or manually
pnpm add eslint-config-maily
```

## Usage

Add the configuration to your `.eslintrc.js` or `.eslintrc.json`:

```js
// .eslintrc.js
module.exports = {
  extends: ["maily"],
};
```

Or in package.json:

```json
{
  "eslintConfig": {
    "extends": ["maily"]
  }
}
```

## Configuration Details

This configuration:

1. Extends the following configs:
   - `next` - Rules from Next.js to catch common issues in Next.js applications
   - `turbo` - Rules optimized for monorepos using Turborepo
   - `prettier` - Disables ESLint rules that might conflict with Prettier

2. Disables some opinionated rules:
   - `@next/next/no-html-link-for-pages` - Allows using regular HTML links
   - `react/jsx-key` - Disables requirement for keys in iterative components (though using keys is still recommended)

## Requirements

- Node.js >= 18.0.0
- npm >= 8.0.0
- ESLint

## Customizing

While it's recommended to use this configuration as-is to maintain consistency, you can extend or override rules in your project's ESLint config:

```js
// .eslintrc.js
module.exports = {
  extends: ["maily"],
  rules: {
    // Your project-specific overrides
    "no-console": "error",
  },
};
```

## Integration with Other Tools

This configuration works with:

- VS Code ESLint extension
- GitHub Actions workflows
- Pre-commit hooks
- Maily's CI/CD pipeline

## Contributing

To modify this shared configuration:

1. Update the rules in `index.js`
2. Test changes with various types of projects in the monorepo
3. Bump the version in `package.json`
4. Submit a PR for review

## License

MIT
