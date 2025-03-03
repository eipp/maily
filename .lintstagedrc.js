module.exports = {
  '*.{js,jsx,ts,tsx}': [
    'eslint --fix',
    'prettier --write',
  ],
  '*.{json,md,yml,yaml}': [
    'prettier --write',
  ],
  '*.{css,scss}': [
    'prettier --write',
  ],
  '*.py': [
    'python -m black',
    'python -m ruff check --fix',
  ],
};