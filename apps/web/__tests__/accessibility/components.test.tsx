import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import { AccessibleTooltip } from '../../components/accessibility/AccessibleTooltip';
import { AccessibleModal } from '../../components/accessibility/AccessibleModal';
import { AccessibleTabs } from '../../components/accessibility/AccessibleTabs';
import { AccessibleAccordion } from '../../components/accessibility/AccessibleAccordion';
import { SkipNavigation } from '../../components/accessibility/SkipNavigation';
import { testAccessibility } from './AccessibilityTests';

// Mock createPortal for modal tests
jest.mock('react-dom', () => {
  const original = jest.requireActual('react-dom');
  return {
    ...original,
    createPortal: (node: React.ReactNode) => node,
  };
});

describe('Accessibility Components', () => {
  describe('AccessibleTooltip', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleTooltip content="Tooltip content">
          <button>Hover me</button>
        </AccessibleTooltip>
      );

      // Show the tooltip
      fireEvent.mouseEnter(screen.getByText('Hover me'));
      await waitFor(() => screen.getByRole('tooltip'));

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should show and hide tooltip on mouse events', async () => {
      render(
        <AccessibleTooltip content="Tooltip content" showDelay={0} hideDelay={0}>
          <button>Hover me</button>
        </AccessibleTooltip>
      );

      // Initially tooltip should not be visible
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

      // Show the tooltip
      fireEvent.mouseEnter(screen.getByText('Hover me'));
      await waitFor(() => screen.getByRole('tooltip'));
      expect(screen.getByRole('tooltip')).toBeInTheDocument();

      // Hide the tooltip
      fireEvent.mouseLeave(screen.getByText('Hover me'));
      await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument());
    });

    it('should show and hide tooltip on focus events', async () => {
      render(
        <AccessibleTooltip content="Tooltip content" showDelay={0} hideDelay={0}>
          <button>Focus me</button>
        </AccessibleTooltip>
      );

      // Initially tooltip should not be visible
      expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

      // Show the tooltip on focus
      fireEvent.focus(screen.getByText('Focus me'));
      await waitFor(() => screen.getByRole('tooltip'));
      expect(screen.getByRole('tooltip')).toBeInTheDocument();

      // Hide the tooltip on blur
      fireEvent.blur(screen.getByText('Focus me'));
      await waitFor(() => expect(screen.queryByRole('tooltip')).not.toBeInTheDocument());
    });
  });

  describe('AccessibleModal', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleModal
          isOpen={true}
          onClose={() => {}}
          title="Test Modal"
        >
          <p>Modal content</p>
        </AccessibleModal>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should render modal when isOpen is true', () => {
      render(
        <AccessibleModal
          isOpen={true}
          onClose={() => {}}
          title="Test Modal"
        >
          <p>Modal content</p>
        </AccessibleModal>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('should not render modal when isOpen is false', () => {
      render(
        <AccessibleModal
          isOpen={false}
          onClose={() => {}}
          title="Test Modal"
        >
          <p>Modal content</p>
        </AccessibleModal>
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', () => {
      const onClose = jest.fn();
      render(
        <AccessibleModal
          isOpen={true}
          onClose={onClose}
          title="Test Modal"
        >
          <p>Modal content</p>
        </AccessibleModal>
      );

      fireEvent.click(screen.getByLabelText('Close'));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('AccessibleTabs', () => {
    const tabs = [
      { id: 'tab1', label: 'Tab 1', content: <p>Content 1</p> },
      { id: 'tab2', label: 'Tab 2', content: <p>Content 2</p> },
      { id: 'tab3', label: 'Tab 3', content: <p>Content 3</p> },
    ];

    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleTabs tabs={tabs} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should render tabs and show the default active tab', () => {
      render(<AccessibleTabs tabs={tabs} />);

      // Check that all tab buttons are rendered
      expect(screen.getByText('Tab 1')).toBeInTheDocument();
      expect(screen.getByText('Tab 2')).toBeInTheDocument();
      expect(screen.getByText('Tab 3')).toBeInTheDocument();

      // Check that the first tab is active by default
      expect(screen.getByText('Tab 1').getAttribute('aria-selected')).toBe('true');
      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.queryByText('Content 2')).not.toBeVisible();
      expect(screen.queryByText('Content 3')).not.toBeVisible();
    });

    it('should change active tab when clicked', () => {
      render(<AccessibleTabs tabs={tabs} />);

      // Click on the second tab
      fireEvent.click(screen.getByText('Tab 2'));

      // Check that the second tab is now active
      expect(screen.getByText('Tab 2').getAttribute('aria-selected')).toBe('true');
      expect(screen.queryByText('Content 1')).not.toBeVisible();
      expect(screen.getByText('Content 2')).toBeInTheDocument();
      expect(screen.queryByText('Content 3')).not.toBeVisible();
    });

    it('should handle keyboard navigation', () => {
      render(<AccessibleTabs tabs={tabs} />);

      // Focus the first tab
      const firstTab = screen.getByText('Tab 1');
      firstTab.focus();

      // Press right arrow to move to the next tab
      fireEvent.keyDown(document.activeElement || document.body, { key: 'ArrowRight' });
      expect(screen.getByText('Tab 2').getAttribute('aria-selected')).toBe('true');

      // Press right arrow again to move to the third tab
      fireEvent.keyDown(document.activeElement || document.body, { key: 'ArrowRight' });
      expect(screen.getByText('Tab 3').getAttribute('aria-selected')).toBe('true');

      // Press left arrow to move back to the second tab
      fireEvent.keyDown(document.activeElement || document.body, { key: 'ArrowLeft' });
      expect(screen.getByText('Tab 2').getAttribute('aria-selected')).toBe('true');
    });
  });

  describe('AccessibleAccordion', () => {
    const accordionItems = [
      { id: 'item1', header: 'Section 1', content: <p>Content for section 1</p> },
      { id: 'item2', header: 'Section 2', content: <p>Content for section 2</p> },
    ];

    it('should have no accessibility violations', async () => {
      const { container } = render(<AccessibleAccordion items={accordionItems} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should expand and collapse items when clicked', () => {
      render(<AccessibleAccordion items={accordionItems} />);

      // Initially all items should be collapsed
      expect(screen.queryByText('Content for section 1')).not.toBeVisible();
      expect(screen.queryByText('Content for section 2')).not.toBeVisible();

      // Click first header to expand
      fireEvent.click(screen.getByText('Section 1'));
      expect(screen.getByText('Content for section 1')).toBeVisible();
      expect(screen.queryByText('Content for section 2')).not.toBeVisible();

      // Click second header to expand (first should collapse)
      fireEvent.click(screen.getByText('Section 2'));
      expect(screen.queryByText('Content for section 1')).not.toBeVisible();
      expect(screen.getByText('Content for section 2')).toBeVisible();
    });

    it('should support keyboard navigation', () => {
      render(<AccessibleAccordion items={accordionItems} />);

      // Focus the first header
      const firstHeader = screen.getByText('Section 1').closest('button');
      firstHeader?.focus();

      // Press Enter to expand
      fireEvent.keyDown(document.activeElement || document.body, { key: 'Enter' });
      expect(screen.getByText('Content for section 1')).toBeVisible();

      // Press down arrow to move focus
      fireEvent.keyDown(document.activeElement || document.body, { key: 'ArrowDown' });
      expect(document.activeElement).toBe(screen.getByText('Section 2').closest('button'));
    });
  });

  describe('SkipNavigation', () => {
    it('should have no accessibility violations', async () => {
      await testAccessibility(SkipNavigation);
    });

    it('should render skip link that becomes visible on focus', () => {
      render(<SkipNavigation />);

      const skipLink = screen.getByText('Skip to main content');

      // Initially the link should be visually hidden
      expect(skipLink).toHaveStyle('transform: translateY(-100%)');

      // When focused, the link should become visible
      fireEvent.focus(skipLink);
      expect(skipLink).toHaveStyle('transform: translateY(0)');

      // When blurred, the link should be hidden again
      fireEvent.blur(skipLink);
      expect(skipLink).toHaveStyle('transform: translateY(-100%)');
    });

    it('should render additional skip links when provided', () => {
      const links = [
        { id: 'content', label: 'content' },
        { id: 'navigation', label: 'navigation' },
      ];

      render(<SkipNavigation links={links} />);

      expect(screen.getByText('Skip to main content')).toBeInTheDocument();
      expect(screen.getByText('Skip to content')).toBeInTheDocument();
      expect(screen.getByText('Skip to navigation')).toBeInTheDocument();
    });
  });
});
