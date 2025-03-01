import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe } from 'jest-axe';
import { AccessibleAccordion } from '../../components/accessibility/AccessibleAccordion';

describe('AccessibleAccordion', () => {
  const mockItems = [
    { id: 'item1', header: 'Section 1', content: <p>Content for section 1</p> },
    { id: 'item2', header: 'Section 2', content: <p>Content for section 2</p> },
    { id: 'item3', header: 'Section 3', content: <p>Content for section 3</p>, disabled: true },
  ];

  it('should have no accessibility violations', async () => {
    const { container } = render(<AccessibleAccordion items={mockItems} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should render all accordion items', () => {
    render(<AccessibleAccordion items={mockItems} />);

    expect(screen.getByText('Section 1')).toBeInTheDocument();
    expect(screen.getByText('Section 2')).toBeInTheDocument();
    expect(screen.getByText('Section 3')).toBeInTheDocument();

    // All panels should be hidden initially
    expect(screen.queryByText('Content for section 1')).not.toBeVisible();
    expect(screen.queryByText('Content for section 2')).not.toBeVisible();
    expect(screen.queryByText('Content for section 3')).not.toBeVisible();
  });

  it('should expand an item when its header is clicked', () => {
    render(<AccessibleAccordion items={mockItems} />);

    // Click on the first header
    fireEvent.click(screen.getByText('Section 1'));

    // First panel should be visible, others hidden
    expect(screen.getByText('Content for section 1')).toBeVisible();
    expect(screen.queryByText('Content for section 2')).not.toBeVisible();
    expect(screen.queryByText('Content for section 3')).not.toBeVisible();
  });

  it('should collapse an expanded item when its header is clicked again', () => {
    render(<AccessibleAccordion items={mockItems} />);

    // Click on the first header to expand
    fireEvent.click(screen.getByText('Section 1'));
    expect(screen.getByText('Content for section 1')).toBeVisible();

    // Click on the first header again to collapse
    fireEvent.click(screen.getByText('Section 1'));
    expect(screen.queryByText('Content for section 1')).not.toBeVisible();
  });

  it('should only allow one expanded item at a time by default', () => {
    render(<AccessibleAccordion items={mockItems} />);

    // Expand the first item
    fireEvent.click(screen.getByText('Section 1'));
    expect(screen.getByText('Content for section 1')).toBeVisible();

    // Expand the second item
    fireEvent.click(screen.getByText('Section 2'));

    // First item should be collapsed, second expanded
    expect(screen.queryByText('Content for section 1')).not.toBeVisible();
    expect(screen.getByText('Content for section 2')).toBeVisible();
  });

  it('should allow multiple expanded items when allowMultiple is true', () => {
    render(<AccessibleAccordion items={mockItems} allowMultiple={true} />);

    // Expand the first item
    fireEvent.click(screen.getByText('Section 1'));
    expect(screen.getByText('Content for section 1')).toBeVisible();

    // Expand the second item
    fireEvent.click(screen.getByText('Section 2'));

    // Both items should be expanded
    expect(screen.getByText('Content for section 1')).toBeVisible();
    expect(screen.getByText('Content for section 2')).toBeVisible();
  });

  it('should respect defaultExpandedIds prop', () => {
    render(
      <AccessibleAccordion
        items={mockItems}
        defaultExpandedIds={['item2']}
      />
    );

    // Second item should be expanded initially
    expect(screen.queryByText('Content for section 1')).not.toBeVisible();
    expect(screen.getByText('Content for section 2')).toBeVisible();
    expect(screen.queryByText('Content for section 3')).not.toBeVisible();
  });

  it('should not toggle disabled items', () => {
    render(<AccessibleAccordion items={mockItems} />);

    // Try to click on the disabled item
    fireEvent.click(screen.getByText('Section 3'));

    // Disabled item should remain collapsed
    expect(screen.queryByText('Content for section 3')).not.toBeVisible();
  });

  it('should call onChange when an item is toggled', () => {
    const handleChange = jest.fn();
    render(
      <AccessibleAccordion
        items={mockItems}
        onChange={handleChange}
      />
    );

    // Expand the first item
    fireEvent.click(screen.getByText('Section 1'));
    expect(handleChange).toHaveBeenCalledWith(['item1']);

    // Expand the second item (which collapses the first)
    fireEvent.click(screen.getByText('Section 2'));
    expect(handleChange).toHaveBeenCalledWith(['item2']);
  });

  it('should support keyboard navigation', () => {
    render(<AccessibleAccordion items={mockItems} />);

    // Focus the first header
    const firstHeader = screen.getByText('Section 1').closest('button');
    firstHeader?.focus();

    // Press down arrow to move to the next header
    fireEvent.keyDown(document.activeElement || document.body, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(screen.getByText('Section 2').closest('button'));

    // Press Enter to expand the second item
    fireEvent.keyDown(document.activeElement || document.body, { key: 'Enter' });
    expect(screen.getByText('Content for section 2')).toBeVisible();

    // Press Home to go to the first header
    fireEvent.keyDown(document.activeElement || document.body, { key: 'Home' });
    expect(document.activeElement).toBe(screen.getByText('Section 1').closest('button'));

    // Press End to go to the last header
    fireEvent.keyDown(document.activeElement || document.body, { key: 'End' });
    expect(document.activeElement).toBe(screen.getByText('Section 3').closest('button'));
  });
});
