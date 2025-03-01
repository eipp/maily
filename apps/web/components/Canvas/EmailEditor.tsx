import React, { useEffect, useRef, useState, useCallback } from 'react';
import { fabric } from 'fabric';
import { useTranslation } from 'react-i18next';
import { useTheme } from 'next-themes';
import { toast } from 'react-hot-toast';
import { useAccessibility } from '../AccessibilityProvider';

interface EmailEditorProps {
  initialContent?: string;
  onChange?: (content: string) => void;
  onSave?: (content: string) => void;
  readOnly?: boolean;
}

export const EmailEditor: React.FC<EmailEditorProps> = ({
  initialContent,
  onChange,
  onSave,
  readOnly = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [canvas, setCanvas] = useState<fabric.Canvas | null>(null);
  const { t } = useTranslation();
  const { theme } = useTheme();
  const { highContrast } = useAccessibility();
  const [focusedObjectIndex, setFocusedObjectIndex] = useState<number>(-1);
  const [canvasObjects, setCanvasObjects] = useState<fabric.Object[]>([]);

  // Keyboard event handler for canvas navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!canvas) return;

    const objects = canvas.getObjects();

    switch (e.key) {
      case 'Tab':
        // Prevent default tab behavior
        e.preventDefault();

        // Move focus to next/previous object
        const newIndex = e.shiftKey
          ? (focusedObjectIndex <= 0 ? objects.length - 1 : focusedObjectIndex - 1)
          : (focusedObjectIndex >= objects.length - 1 ? 0 : focusedObjectIndex + 1);

        setFocusedObjectIndex(newIndex);

        if (objects[newIndex]) {
          canvas.setActiveObject(objects[newIndex]);
          canvas.renderAll();

          // Announce to screen readers
          announceToScreenReader(`Selected ${objects[newIndex].type}`);
        }
        break;

      case 'Enter':
      case ' ':
        // Activate the currently focused object
        if (focusedObjectIndex >= 0 && objects[focusedObjectIndex]) {
          e.preventDefault();
          // Trigger edit mode or action for the object
          if (objects[focusedObjectIndex].type === 'i-text') {
            canvas.setActiveObject(objects[focusedObjectIndex]);
            (objects[focusedObjectIndex] as fabric.IText).enterEditing();
            canvas.renderAll();
          }
        }
        break;

      case 'Delete':
      case 'Backspace':
        // Delete the currently focused object
        if (focusedObjectIndex >= 0 && objects[focusedObjectIndex]) {
          e.preventDefault();
          canvas.remove(objects[focusedObjectIndex]);
          setFocusedObjectIndex(-1);
          canvas.renderAll();

          // Update objects list
          setCanvasObjects(canvas.getObjects());

          // Announce to screen readers
          announceToScreenReader('Object deleted');
        }
        break;

      case 'Escape':
        // Exit editing mode or deselect object
        canvas.discardActiveObject();
        setFocusedObjectIndex(-1);
        canvas.renderAll();
        break;
    }
  }, [canvas, focusedObjectIndex]);

  // Function to announce messages to screen readers
  const announceToScreenReader = (message: string) => {
    const announcement = document.getElementById('canvas-a11y-announcer');
    if (announcement) {
      announcement.textContent = message;
    }
  };

  useEffect(() => {
    if (canvasRef.current && !canvas) {
      const fabricCanvas = new fabric.Canvas(canvasRef.current, {
        width: 800,
        height: 1200,
        backgroundColor: highContrast ? '#000000' : (theme === 'dark' ? '#1a1a1a' : '#ffffff'),
      });

      setCanvas(fabricCanvas);

      // Load initial content if provided
      if (initialContent) {
        fabricCanvas.loadFromJSON(initialContent, () => {
          fabricCanvas.renderAll();
          setCanvasObjects(fabricCanvas.getObjects());
        });
      }

      // Set up event listeners
      fabricCanvas.on('object:modified', () => {
        const content = fabricCanvas.toJSON();
        onChange?.(JSON.stringify(content));
        setCanvasObjects(fabricCanvas.getObjects());
      });

      fabricCanvas.on('object:added', () => {
        setCanvasObjects(fabricCanvas.getObjects());
      });

      fabricCanvas.on('object:removed', () => {
        setCanvasObjects(fabricCanvas.getObjects());
      });

      // Clean up
      return () => {
        fabricCanvas.dispose();
      };
    }
  }, [initialContent, onChange, theme, highContrast]);

  // Add keyboard event listeners
  useEffect(() => {
    const container = canvasContainerRef.current;
    if (container) {
      container.addEventListener('keydown', handleKeyDown);

      return () => {
        container.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [handleKeyDown]);

  // Update canvas when high contrast mode changes
  useEffect(() => {
    if (canvas) {
      canvas.setBackgroundColor(
        highContrast ? '#000000' : (theme === 'dark' ? '#1a1a1a' : '#ffffff'),
        () => canvas.renderAll()
      );
    }
  }, [highContrast, theme, canvas]);

  const handleAddText = () => {
    if (!canvas || readOnly) return;

    const text = new fabric.IText(t('canvas.defaultText'), {
      left: 50,
      top: 50,
      fontSize: 20,
      fill: theme === 'dark' ? '#ffffff' : '#000000',
    });

    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
  };

  const handleAddImage = async (file: File) => {
    if (!canvas || readOnly) return;

    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        fabric.Image.fromURL(e.target?.result as string, (img) => {
          img.scaleToWidth(200);
          canvas.add(img);
          canvas.renderAll();
        });
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error(t('canvas.imageError'));
    }
  };

  const handleSave = () => {
    if (!canvas) return;
    const content = canvas.toJSON();
    onSave?.(JSON.stringify(content));
    toast.success(t('canvas.saveSuccess'));
  };

  return (
    <div
      className="email-editor-container"
      ref={canvasContainerRef}
      tabIndex={0} // Make container focusable
      aria-label={t('Email editor canvas')}
      role="application"
    >
      {/* Screen reader announcer */}
      <div
        id="canvas-a11y-announcer"
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      ></div>

      <canvas
        ref={canvasRef}
        aria-label={t('Email content canvas')}
      />

      {!readOnly && (
        <div className="email-editor-controls" role="toolbar" aria-label={t('Email editor controls')}>
          <button
            onClick={() => handleAddText()}
            aria-label={t('Add text')}
            className="editor-control-button"
          >
            {t('Add Text')}
          </button>
          <label
            htmlFor="image-upload"
            className="editor-control-button"
            tabIndex={0}
            role="button"
            aria-label={t('Add image')}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                document.getElementById('image-upload')?.click();
              }
            }}
          >
            {t('Add Image')}
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  handleAddImage(e.target.files[0]);
                }
              }}
              aria-hidden="true"
            />
          </label>
          <button
            onClick={() => handleSave()}
            aria-label={t('Save email')}
            className="editor-control-button"
          >
            {t('Save')}
          </button>
        </div>
      )}

      {/* Accessible object list for keyboard navigation */}
      <div className="sr-only">
        <h2 id="canvas-objects-heading">{t('Canvas Objects')}</h2>
        <ul aria-labelledby="canvas-objects-heading">
          {canvasObjects.map((obj, index) => (
            <li key={index}>
              <button
                onClick={() => {
                  setFocusedObjectIndex(index);
                  canvas?.setActiveObject(obj);
                  canvas?.renderAll();
                }}
                aria-pressed={focusedObjectIndex === index}
              >
                {obj.type} {index + 1}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
