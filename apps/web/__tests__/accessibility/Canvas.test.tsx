import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { EmailEditor } from '../../components/Canvas/EmailEditor';
import { CollaborativeCanvas } from '../../components/Canvas/CollaborativeCanvas';
import { testAccessibility } from './AccessibilityTests';

// Mock the fabric canvas to avoid DOM errors in tests
jest.mock('fabric', () => ({
  fabric: {
    Canvas: jest.fn().mockImplementation(() => ({
      loadFromJSON: jest.fn(),
      renderAll: jest.fn(),
      on: jest.fn(),
      dispose: jest.fn(),
      toJSON: jest.fn().mockReturnValue({}),
      add: jest.fn(),
      setActiveObject: jest.fn(),
      getActiveObject: jest.fn(),
    })),
    IText: jest.fn().mockImplementation(() => ({})),
    Image: {
      fromURL: jest.fn().mockImplementation((url, callback) => {
        callback({});
      }),
    },
  },
}));

describe('Canvas Components Accessibility', () => {
  it('EmailEditor should have no accessibility violations', async () => {
    const { container } = render(
      <EmailEditor
        initialContent="{}"
        onChange={() => {}}
        onSave={() => {}}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('CollaborativeCanvas should have no accessibility violations', async () => {
    await testAccessibility(CollaborativeCanvas, {
      documentId: 'test-doc',
      readOnly: false,
    });
  });

  it('Canvas components should have proper keyboard navigation', () => {
    render(
      <EmailEditor
        initialContent="{}"
        onChange={() => {}}
        onSave={() => {}}
      />
    );

    // Check for keyboard accessible controls
    const controls = screen.getAllByRole('button');
    expect(controls.length).toBeGreaterThan(0);

    // Each control should have a tabIndex
    controls.forEach(control => {
      expect(control).toHaveAttribute('tabIndex', expect.any(String));
    });
  });

  it('Canvas components should have proper ARIA attributes', () => {
    render(
      <EmailEditor
        initialContent="{}"
        onChange={() => {}}
        onSave={() => {}}
      />
    );

    // Check for proper ARIA labeling
    const canvas = screen.getByRole('application');
    expect(canvas).toHaveAttribute('aria-label', expect.any(String));
  });
});
