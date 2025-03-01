import React, { useRef, useState } from 'react';
import { useButton } from '@react-aria/button';
import { useDatePicker } from '@react-aria/datepicker';
import { useDatePickerState } from '@react-stately/datepicker';
import { useCalendar } from '@react-aria/calendar';
import { useCalendarState } from '@react-stately/calendar';
import { useDialog } from '@react-aria/dialog';
import { FocusScope } from '@react-aria/focus';
import { useOverlay, useOverlayTrigger } from '@react-aria/overlays';
import { useLocale } from '@react-aria/i18n';
import { createCalendar, getLocalTimeZone } from '@internationalized/date';
import { OverlayContainer } from '@react-aria/overlays';
import type { DateValue } from '@react-types/calendar';

interface AccessibleDatePickerProps {
  label: string;
  value?: DateValue;
  onChange?: (date: DateValue) => void;
  minValue?: DateValue;
  maxValue?: DateValue;
  isDisabled?: boolean;
  isRequired?: boolean;
  className?: string;
}

/**
 * An accessible date picker component built with React Aria
 * This component ensures proper keyboard navigation, focus management,
 * and screen reader support for date selection.
 */
const AccessibleDatePicker: React.FC<AccessibleDatePickerProps> = (props) => {
  const { locale } = useLocale();
  const state = useDatePickerState({
    ...props,
    locale,
    createCalendar
  });

  const ref = useRef<HTMLDivElement>(null);
  const { labelProps, fieldProps, buttonProps, dialogProps, calendarProps } = useDatePicker(
    props,
    state,
    ref
  );

  return (
    <div className="relative" ref={ref}>
      <div className="flex flex-col">
        <label {...labelProps} className="text-sm font-medium text-gray-700 mb-1">
          {props.label}
        </label>
        <div className="flex">
          <DateField
            {...fieldProps}
            state={state}
            className={`px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 ${props.className || ''}`}
          />
          <DatePickerButton
            {...buttonProps}
            isDisabled={props.isDisabled}
          />
        </div>
      </div>
      {state.isOpen && (
        <OverlayContainer>
          <DatePickerDialog
            {...dialogProps}
            state={state}
            calendarProps={calendarProps}
          />
        </OverlayContainer>
      )}
    </div>
  );
};

// DateField component to display the selected date
interface DateFieldProps {
  state: any;
  className?: string;
}

const DateField: React.FC<DateFieldProps> = ({ state, className }) => {
  const inputRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={inputRef}
      className={`flex items-center ${className}`}
    >
      {state.value
        ? state.value.toDate(getLocalTimeZone()).toLocaleDateString()
        : 'Select a date'}
    </div>
  );
};

// Button to open the date picker dialog
interface DatePickerButtonProps {
  isDisabled?: boolean;
}

const DatePickerButton: React.FC<DatePickerButtonProps & React.HTMLAttributes<HTMLButtonElement>> = (props) => {
  const ref = useRef<HTMLButtonElement>(null);
  const { buttonProps } = useButton(props, ref);

  return (
    <button
      {...buttonProps}
      ref={ref}
      className={`px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md text-gray-600 hover:bg-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500 ${props.isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    </button>
  );
};

// Dialog containing the calendar
interface DatePickerDialogProps {
  state: any;
  calendarProps: any;
}

const DatePickerDialog: React.FC<DatePickerDialogProps & React.HTMLAttributes<HTMLDivElement>> = (props) => {
  const { state, calendarProps } = props;
  const ref = useRef<HTMLDivElement>(null);
  const { overlayProps } = useOverlay(
    {
      isOpen: state.isOpen,
      onClose: () => state.setOpen(false),
      isDismissable: true
    },
    ref
  );

  const { dialogProps } = useDialog({}, ref);

  return (
    <FocusScope contain restoreFocus autoFocus>
      <div
        {...overlayProps}
        {...dialogProps}
        ref={ref}
        className="absolute z-10 mt-2 bg-white border border-gray-300 rounded-md shadow-lg p-4"
      >
        <Calendar {...calendarProps} />
      </div>
    </FocusScope>
  );
};

// Calendar component
interface CalendarProps {
  value?: DateValue;
  onChange?: (date: DateValue) => void;
}

const Calendar: React.FC<CalendarProps> = (props) => {
  const { locale } = useLocale();
  const state = useCalendarState({
    ...props,
    locale,
    createCalendar
  });

  const ref = useRef<HTMLDivElement>(null);
  const { calendarProps, prevButtonProps, nextButtonProps, title } = useCalendar(
    props,
    state,
    ref
  );

  return (
    <div {...calendarProps} ref={ref} className="calendar">
      <div className="flex items-center justify-between mb-4">
        <button
          {...prevButtonProps}
          className="p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h2 className="text-lg font-semibold">{title}</h2>
        <button
          {...nextButtonProps}
          className="p-1 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {state.getDatesInWeek(0).map((date, i) => (
          <div key={i} className="text-center text-sm font-medium text-gray-700 py-1">
            {date ? date.toDate(getLocalTimeZone()).toLocaleDateString(locale, { weekday: 'narrow' }) : ''}
          </div>
        ))}
        {state.visibleRange.start.cycle('day', 7 * 6).map((date, i) => (
          <CalendarCell
            key={i}
            state={state}
            date={date}
            currentMonth={state.visibleRange.start.month}
          />
        ))}
      </div>
    </div>
  );
};

// Calendar cell component
interface CalendarCellProps {
  state: any;
  date: DateValue;
  currentMonth: number;
}

const CalendarCell: React.FC<CalendarCellProps> = ({ state, date, currentMonth }) => {
  const ref = useRef<HTMLDivElement>(null);
  const isSelected = state.isSelected(date);
  const isDisabled = state.isDisabled(date);
  const isOutsideMonth = date.month !== currentMonth;

  const cellProps = {
    onClick: () => {
      if (!isDisabled) {
        state.selectDate(date);
      }
    }
  };

  return (
    <div
      ref={ref}
      {...cellProps}
      className={`
        text-center py-2 rounded-md cursor-pointer text-sm
        ${isSelected ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${isOutsideMonth ? 'text-gray-400' : 'text-gray-800'}
      `}
      aria-selected={isSelected}
      aria-disabled={isDisabled}
    >
      {date.day}
    </div>
  );
};

export default AccessibleDatePicker;
