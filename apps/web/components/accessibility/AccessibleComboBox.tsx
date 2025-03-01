import React, { useRef, useState, useEffect } from 'react';
import { useComboBox } from '@react-aria/combobox';
import { useComboBoxState } from '@react-stately/combobox';
import { useButton } from '@react-aria/button';
import { useFilter } from '@react-aria/i18n';
import { FocusScope } from '@react-aria/focus';
import { useOverlay, DismissButton } from '@react-aria/overlays';

interface Option {
  id: string;
  name: string;
}

interface AccessibleComboBoxProps {
  label: string;
  options: Option[];
  onSelectionChange?: (selectedOption: Option | null) => void;
  placeholder?: string;
  isDisabled?: boolean;
  isRequired?: boolean;
  className?: string;
}

/**
 * An accessible combo box component built with React Aria
 * This component provides an accessible autocomplete input with dropdown
 * that supports keyboard navigation, screen readers, and proper ARIA attributes.
 */
const AccessibleComboBox: React.FC<AccessibleComboBoxProps> = (props) => {
  const { label, options, onSelectionChange, placeholder = 'Select an option', isDisabled = false, isRequired = false, className = '' } = props;

  // State for the input value and selected option
  const [inputValue, setInputValue] = useState('');
  const [selectedOption, setSelectedOption] = useState<Option | null>(null);

  // Filter options based on input value
  const { contains } = useFilter({ sensitivity: 'base' });
  const filteredOptions = options.filter(option =>
    contains(option.name, inputValue)
  );

  // Refs for DOM elements
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listBoxRef = useRef<HTMLUListElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  // State for the combobox
  const [isOpen, setIsOpen] = useState(false);

  // Handle input change
  const handleInputChange = (value: string) => {
    setInputValue(value);
    setIsOpen(true);
  };

  // Handle option selection
  const handleSelect = (option: Option) => {
    setSelectedOption(option);
    setInputValue(option.name);
    setIsOpen(false);

    if (onSelectionChange) {
      onSelectionChange(option);
    }

    // Focus the input after selection
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Toggle the dropdown
  const toggleDropdown = () => {
    setIsOpen(!isOpen);

    // Focus the input when opening
    if (!isOpen && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  };

  // Close the dropdown when clicking outside
  const { overlayProps } = useOverlay(
    {
      isOpen,
      onClose: () => setIsOpen(false),
      shouldCloseOnBlur: true,
      isDismissable: true
    },
    popoverRef
  );

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        setIsOpen(false);
        break;
      case 'ArrowDown':
        if (!isOpen) {
          setIsOpen(true);
        }
        if (listBoxRef.current && listBoxRef.current.firstChild) {
          (listBoxRef.current.firstChild as HTMLElement).focus();
        }
        e.preventDefault();
        break;
      case 'Enter':
        if (isOpen && filteredOptions.length > 0) {
          handleSelect(filteredOptions[0]);
          e.preventDefault();
        }
        break;
    }
  };

  // Handle option keyboard navigation
  const handleOptionKeyDown = (e: React.KeyboardEvent, option: Option) => {
    switch (e.key) {
      case 'Enter':
      case 'Space':
        handleSelect(option);
        e.preventDefault();
        break;
      case 'Escape':
        setIsOpen(false);
        if (inputRef.current) {
          inputRef.current.focus();
        }
        e.preventDefault();
        break;
      case 'ArrowUp':
        const prevSibling = (e.currentTarget as HTMLElement).previousElementSibling as HTMLElement;
        if (prevSibling) {
          prevSibling.focus();
        } else if (inputRef.current) {
          inputRef.current.focus();
        }
        e.preventDefault();
        break;
      case 'ArrowDown':
        const nextSibling = (e.currentTarget as HTMLElement).nextElementSibling as HTMLElement;
        if (nextSibling) {
          nextSibling.focus();
        }
        e.preventDefault();
        break;
    }
  };

  return (
    <div className={`relative ${className}`}>
      <label
        htmlFor="combobox-input"
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
        {isRequired && <span className="text-red-500 ml-1">*</span>}
      </label>

      <div className="relative">
        <input
          ref={inputRef}
          id="combobox-input"
          type="text"
          className={`
            w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm
            focus:outline-none focus:ring-blue-500 focus:border-blue-500
            ${isDisabled ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''}
          `}
          value={inputValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label={label}
          aria-autocomplete="list"
          aria-controls={isOpen ? "combobox-listbox" : undefined}
          aria-expanded={isOpen}
          aria-required={isRequired}
          disabled={isDisabled}
          role="combobox"
        />

        <button
          ref={buttonRef}
          type="button"
          className={`
            absolute inset-y-0 right-0 flex items-center px-2
            text-gray-500 hover:text-gray-700 focus:outline-none
            ${isDisabled ? 'cursor-not-allowed' : ''}
          `}
          onClick={toggleDropdown}
          aria-label={isOpen ? "Close dropdown" : "Open dropdown"}
          disabled={isDisabled}
          tabIndex={-1}
        >
          <svg
            className={`w-5 h-5 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isOpen && (
        <FocusScope restoreFocus>
          <div
            ref={popoverRef}
            {...overlayProps}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
          >
            <DismissButton onDismiss={() => setIsOpen(false)} />

            <ul
              ref={listBoxRef}
              id="combobox-listbox"
              role="listbox"
              aria-label={`${label} options`}
              className="py-1"
            >
              {filteredOptions.length > 0 ? (
                filteredOptions.map((option) => (
                  <li
                    key={option.id}
                    id={`option-${option.id}`}
                    role="option"
                    aria-selected={selectedOption?.id === option.id}
                    tabIndex={0}
                    className={`
                      px-3 py-2 cursor-pointer text-sm
                      ${selectedOption?.id === option.id ? 'bg-blue-100 text-blue-900' : 'text-gray-900 hover:bg-gray-100'}
                      focus:bg-blue-100 focus:text-blue-900 focus:outline-none
                    `}
                    onClick={() => handleSelect(option)}
                    onKeyDown={(e) => handleOptionKeyDown(e, option)}
                  >
                    {option.name}
                  </li>
                ))
              ) : (
                <li className="px-3 py-2 text-sm text-gray-500">No options found</li>
              )}
            </ul>

            <DismissButton onDismiss={() => setIsOpen(false)} />
          </div>
        </FocusScope>
      )}
    </div>
  );
};

export default AccessibleComboBox;
