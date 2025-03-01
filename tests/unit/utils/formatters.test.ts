import { formatDate, formatCurrency, formatFileSize, truncateText } from '@/utils/formatters';

describe('Formatting Utilities', () => {
  describe('formatDate', () => {
    it('formats date in default format', () => {
      const date = new Date('2024-02-24T12:00:00Z');
      expect(formatDate(date)).toBe('Feb 24, 2024');
    });

    it('formats date with custom format', () => {
      const date = new Date('2024-02-24T12:00:00Z');
      expect(formatDate(date, 'YYYY-MM-DD')).toBe('2024-02-24');
    });

    it('handles invalid dates', () => {
      expect(formatDate(new Date('invalid'))).toBe('Invalid Date');
    });
  });

  describe('formatCurrency', () => {
    it('formats USD currency', () => {
      expect(formatCurrency(1234.56, 'USD')).toBe('$1,234.56');
    });

    it('formats EUR currency', () => {
      expect(formatCurrency(1234.56, 'EUR')).toBe('€1,234.56');
    });

    it('handles zero and negative values', () => {
      expect(formatCurrency(0, 'USD')).toBe('$0.00');
      expect(formatCurrency(-1234.56, 'USD')).toBe('-$1,234.56');
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes', () => {
      expect(formatFileSize(500)).toBe('500 B');
    });

    it('formats kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1.0 KB');
    });

    it('formats megabytes', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
    });

    it('formats gigabytes', () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1.0 GB');
    });

    it('handles zero and negative values', () => {
      expect(formatFileSize(0)).toBe('0 B');
      expect(formatFileSize(-1024)).toBe('Invalid size');
    });
  });

  describe('truncateText', () => {
    it('truncates text to specified length', () => {
      expect(truncateText('This is a long text', 10)).toBe('This is...');
    });

    it('does not truncate text shorter than limit', () => {
      expect(truncateText('Short', 10)).toBe('Short');
    });

    it('handles empty string', () => {
      expect(truncateText('', 10)).toBe('');
    });

    it('handles custom ellipsis', () => {
      expect(truncateText('This is a long text', 10, '...')).toBe('This is...');
    });
  });
});
