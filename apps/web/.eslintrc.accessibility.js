module.exports = {
  extends: [
    './.eslintrc.js',
    'plugin:jsx-a11y/recommended',
  ],
  plugins: [
    'jsx-a11y',
  ],
  rules: {
    // Enforce ARIA roles are valid and not abstract
    'jsx-a11y/aria-role': ['error', { ignoreNonDOM: true }],

    // Enforce all elements that require alternative text have meaningful information
    'jsx-a11y/alt-text': 'error',

    // Enforce all aria-* props are valid
    'jsx-a11y/aria-props': 'error',

    // Enforce ARIA state and property values are valid
    'jsx-a11y/aria-proptypes': 'error',

    // Enforce that elements with ARIA roles must have all required attributes for that role
    'jsx-a11y/role-has-required-aria-props': 'error',

    // Enforce that elements with explicit or implicit roles defined contain only aria-* properties supported by that role
    'jsx-a11y/role-supports-aria-props': 'error',

    // Enforce tabIndex value is not greater than zero
    'jsx-a11y/tabindex-no-positive': 'error',

    // Enforce that a label tag has a text label and an associated control
    'jsx-a11y/label-has-associated-control': [
      'error',
      {
        labelComponents: ['CustomLabel'],
        labelAttributes: ['label'],
        controlComponents: ['CustomInput'],
        assert: 'both',
        depth: 3,
      },
    ],

    // Enforce that mouse events are accompanied by keyboard events
    'jsx-a11y/mouse-events-have-key-events': 'error',

    // Enforce that elements with onClick handlers must be focusable
    'jsx-a11y/click-events-have-key-events': 'error',

    // Enforce that non-interactive elements don't have interactive handlers
    'jsx-a11y/no-noninteractive-element-interactions': 'error',

    // Enforce explicit role property is not the same as implicit/default role property on element
    'jsx-a11y/no-redundant-roles': 'error',

    // Enforce that autoFocus prop is not used on elements
    'jsx-a11y/no-autofocus': 'warn',

    // Enforce that heading elements (h1, h2, etc.) have content
    'jsx-a11y/heading-has-content': 'error',

    // Enforce that anchor elements have content
    'jsx-a11y/anchor-has-content': 'error',

    // Enforce that anchors have valid targets
    'jsx-a11y/anchor-is-valid': 'error',
  },
};
