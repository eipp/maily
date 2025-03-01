import { test, expect } from '@playwright/test';
import { performance } from 'perf_hooks';

// Performance thresholds in milliseconds
const RENDER_TIME_THRESHOLD = 100;
const INTERACTION_TIME_THRESHOLD = 50;
const ELEMENT_COUNT_THRESHOLD = 1000;

test.describe('Canvas Component Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', process.env.TEST_USER_EMAIL || 'test@example.com');
    await page.fill('input[name="password"]', process.env.TEST_USER_PASSWORD || 'password');
    await page.click('button[type="submit"]');

    // Navigate to the canvas page
    await page.goto('/editor/canvas');

    // Wait for the canvas to be fully loaded
    await page.waitForSelector('.canvas-container', { state: 'visible' });
  });

  test('Canvas initial render performance', async ({ page }) => {
    // Measure the time it takes to render the canvas
    const renderTime = await page.evaluate(() => {
      performance.mark('canvas-render-start');

      // Force a re-render of the canvas
      document.querySelector('.canvas-container').style.display = 'none';
      document.querySelector('.canvas-container').offsetHeight; // Force reflow
      document.querySelector('.canvas-container').style.display = 'block';

      // Wait for the render to complete
      return new Promise(resolve => {
        requestAnimationFrame(() => {
          performance.mark('canvas-render-end');
          performance.measure('canvas-render', 'canvas-render-start', 'canvas-render-end');
          const measurements = performance.getEntriesByName('canvas-render');
          resolve(measurements[0].duration);
        });
      });
    });

    console.log(`Canvas render time: ${renderTime.toFixed(2)}ms`);
    expect(renderTime).toBeLessThan(RENDER_TIME_THRESHOLD);
  });

  test('Canvas element addition performance', async ({ page }) => {
    // Measure the time it takes to add an element to the canvas
    const addElementTime = await page.evaluate(() => {
      performance.mark('add-element-start');

      // Simulate adding an element to the canvas
      const addElementButton = document.querySelector('.add-element-button');
      addElementButton.click();

      return new Promise(resolve => {
        // Wait for the element to be added
        const checkInterval = setInterval(() => {
          const elements = document.querySelectorAll('.canvas-element');
          if (elements.length > 0) {
            clearInterval(checkInterval);
            performance.mark('add-element-end');
            performance.measure('add-element', 'add-element-start', 'add-element-end');
            const measurements = performance.getEntriesByName('add-element');
            resolve(measurements[0].duration);
          }
        }, 10);
      });
    });

    console.log(`Element addition time: ${addElementTime.toFixed(2)}ms`);
    expect(addElementTime).toBeLessThan(INTERACTION_TIME_THRESHOLD);
  });

  test('Canvas drag and drop performance', async ({ page }) => {
    // Add an element to the canvas first
    await page.click('.add-element-button');
    await page.waitForSelector('.canvas-element');

    // Measure the time it takes to drag and drop an element
    const dragTime = await page.evaluate(() => {
      performance.mark('drag-start');

      // Simulate dragging an element
      const element = document.querySelector('.canvas-element');
      const rect = element.getBoundingClientRect();

      // Create and dispatch mouse events for drag and drop
      const mouseDown = new MouseEvent('mousedown', {
        bubbles: true,
        clientX: rect.left + 10,
        clientY: rect.top + 10
      });

      const mouseMove = new MouseEvent('mousemove', {
        bubbles: true,
        clientX: rect.left + 100,
        clientY: rect.top + 100
      });

      const mouseUp = new MouseEvent('mouseup', {
        bubbles: true,
        clientX: rect.left + 100,
        clientY: rect.top + 100
      });

      element.dispatchEvent(mouseDown);

      return new Promise(resolve => {
        setTimeout(() => {
          element.dispatchEvent(mouseMove);

          setTimeout(() => {
            element.dispatchEvent(mouseUp);
            performance.mark('drag-end');
            performance.measure('drag', 'drag-start', 'drag-end');
            const measurements = performance.getEntriesByName('drag');
            resolve(measurements[0].duration);
          }, 50);
        }, 50);
      });
    });

    console.log(`Drag and drop time: ${dragTime.toFixed(2)}ms`);
    expect(dragTime).toBeLessThan(INTERACTION_TIME_THRESHOLD * 2); // Allow more time for drag operations
  });

  test('Canvas with many elements performance', async ({ page }) => {
    // Add many elements to the canvas and measure performance
    const manyElementsPerformance = await page.evaluate((threshold) => {
      // Function to add elements to the canvas
      const addElements = (count) => {
        for (let i = 0; i < count; i++) {
          const element = document.createElement('div');
          element.className = 'canvas-element';
          element.style.position = 'absolute';
          element.style.left = `${Math.random() * 800}px`;
          element.style.top = `${Math.random() * 600}px`;
          element.style.width = '100px';
          element.style.height = '50px';
          element.style.backgroundColor = '#f0f0f0';
          element.style.border = '1px solid #ccc';
          element.textContent = `Element ${i}`;

          document.querySelector('.canvas-container').appendChild(element);
        }
      };

      // Add many elements
      performance.mark('many-elements-start');
      addElements(threshold);
      performance.mark('many-elements-end');

      // Measure the time it took to add all elements
      performance.measure('many-elements', 'many-elements-start', 'many-elements-end');
      const addTime = performance.getEntriesByName('many-elements')[0].duration;

      // Measure scroll performance
      performance.mark('scroll-start');
      document.querySelector('.canvas-container').scrollTop = 100;
      performance.mark('scroll-end');
      performance.measure('scroll', 'scroll-start', 'scroll-end');
      const scrollTime = performance.getEntriesByName('scroll')[0].duration;

      // Count the actual number of elements rendered
      const elementCount = document.querySelectorAll('.canvas-element').length;

      return {
        addTime,
        scrollTime,
        elementCount
      };
    }, ELEMENT_COUNT_THRESHOLD);

    console.log(`Time to add ${manyElementsPerformance.elementCount} elements: ${manyElementsPerformance.addTime.toFixed(2)}ms`);
    console.log(`Scroll time with many elements: ${manyElementsPerformance.scrollTime.toFixed(2)}ms`);

    // Verify that the canvas can handle the threshold number of elements
    expect(manyElementsPerformance.elementCount).toBeGreaterThanOrEqual(ELEMENT_COUNT_THRESHOLD);

    // Verify that scrolling is still performant with many elements
    expect(manyElementsPerformance.scrollTime).toBeLessThan(INTERACTION_TIME_THRESHOLD);
  });

  test('Canvas memory usage', async ({ page }) => {
    // Measure memory usage before and after adding many elements
    const memoryUsage = await page.evaluate(async (threshold) => {
      // Get initial memory usage
      const initialMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;

      // Add many elements to the canvas
      const addElements = (count) => {
        for (let i = 0; i < count; i++) {
          const element = document.createElement('div');
          element.className = 'canvas-element';
          element.style.position = 'absolute';
          element.style.left = `${Math.random() * 800}px`;
          element.style.top = `${Math.random() * 600}px`;
          element.style.width = '100px';
          element.style.height = '50px';
          element.style.backgroundColor = '#f0f0f0';
          element.style.border = '1px solid #ccc';
          element.textContent = `Element ${i}`;

          document.querySelector('.canvas-container').appendChild(element);
        }
      };

      addElements(threshold / 10); // Add 10% of the threshold to avoid browser crashes

      // Force garbage collection if possible
      if (window.gc) {
        window.gc();
      }

      // Get final memory usage
      const finalMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;

      return {
        initialMemory,
        finalMemory,
        difference: finalMemory - initialMemory,
        supported: !!performance.memory
      };
    }, ELEMENT_COUNT_THRESHOLD);

    if (memoryUsage.supported) {
      console.log(`Initial memory usage: ${(memoryUsage.initialMemory / 1024 / 1024).toFixed(2)}MB`);
      console.log(`Final memory usage: ${(memoryUsage.finalMemory / 1024 / 1024).toFixed(2)}MB`);
      console.log(`Memory usage difference: ${(memoryUsage.difference / 1024 / 1024).toFixed(2)}MB`);

      // Check that memory usage is reasonable (less than 100MB increase)
      expect(memoryUsage.difference).toBeLessThan(100 * 1024 * 1024);
    } else {
      console.log('Memory usage measurement not supported in this browser');
    }
  });

  test('Canvas resize performance', async ({ page }) => {
    // Measure the time it takes to resize the canvas
    const resizeTime = await page.evaluate(() => {
      performance.mark('resize-start');

      // Resize the canvas container
      const container = document.querySelector('.canvas-container');
      const originalWidth = container.offsetWidth;
      const originalHeight = container.offsetHeight;

      container.style.width = `${originalWidth * 1.5}px`;
      container.style.height = `${originalHeight * 1.5}px`;

      return new Promise(resolve => {
        // Wait for the resize to complete
        requestAnimationFrame(() => {
          performance.mark('resize-end');
          performance.measure('resize', 'resize-start', 'resize-end');
          const measurements = performance.getEntriesByName('resize');

          // Restore original size
          container.style.width = `${originalWidth}px`;
          container.style.height = `${originalHeight}px`;

          resolve(measurements[0].duration);
        });
      });
    });

    console.log(`Canvas resize time: ${resizeTime.toFixed(2)}ms`);
    expect(resizeTime).toBeLessThan(INTERACTION_TIME_THRESHOLD);
  });

  test('Canvas rendering FPS', async ({ page }) => {
    // Measure the FPS during canvas interactions
    const fps = await page.evaluate(() => {
      let frameCount = 0;
      let lastTime = performance.now();

      // Start counting frames
      const countFrames = () => {
        frameCount++;
        requestAnimationFrame(countFrames);
      };

      requestAnimationFrame(countFrames);

      // Simulate some interactions
      const container = document.querySelector('.canvas-container');

      // Add some elements
      for (let i = 0; i < 10; i++) {
        const element = document.createElement('div');
        element.className = 'canvas-element';
        element.style.position = 'absolute';
        element.style.left = `${Math.random() * 800}px`;
        element.style.top = `${Math.random() * 600}px`;
        element.style.width = '100px';
        element.style.height = '50px';
        element.style.backgroundColor = '#f0f0f0';
        element.style.border = '1px solid #ccc';
        element.textContent = `Element ${i}`;

        container.appendChild(element);
      }

      // Simulate scrolling
      let scrollPos = 0;
      const scrollInterval = setInterval(() => {
        container.scrollTop = scrollPos;
        scrollPos += 10;
        if (scrollPos > 200) {
          scrollPos = 0;
        }
      }, 16); // ~60fps

      // Measure for 1 second
      return new Promise(resolve => {
        setTimeout(() => {
          const currentTime = performance.now();
          const elapsedTime = currentTime - lastTime;
          const calculatedFps = frameCount / (elapsedTime / 1000);

          // Clean up
          clearInterval(scrollInterval);

          resolve(calculatedFps);
        }, 1000);
      });
    });

    console.log(`Canvas rendering FPS: ${fps.toFixed(2)}`);
    expect(fps).toBeGreaterThan(30); // Expect at least 30 FPS for smooth interaction
  });
});
