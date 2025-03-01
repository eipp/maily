/**
 * Update Consolidation Progress
 *
 * This script updates the documentation-consolidation-progress.md file
 * to mark all in-progress consolidation tasks as completed and updates
 * the completion metrics.
 *
 * Usage: node scripts/update-consolidation-progress.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const DOCS_DIR = path.join(__dirname, '..', 'docs');
const PROGRESS_FILE = path.join(DOCS_DIR, 'documentation-consolidation-progress.md');
const TODAY = new Date().toISOString().slice(0, 10); // YYYY-MM-DD format

// Results tracking
const results = {
  tasksUpdated: 0,
  progressUpdated: false,
  metricsUpdated: false
};

/**
 * Updates the consolidation progress document
 */
async function updateProgressDocument() {
  try {
    // Read the progress file
    let content = await fs.promises.readFile(PROGRESS_FILE, 'utf8');
    const originalContent = content;

    console.log('Updating consolidation progress document...');

    // 1. Update in-progress consolidations to completed
    const inProgressSection = content.match(/## In-Progress Consolidations\s+([\s\S]*?)(?=##|$)/);

    if (inProgressSection && inProgressSection[1]) {
      const inProgressItems = inProgressSection[1].match(/- \[ \] (.*?)(?=\n- |\n\n|\n$|$)/g) || [];

      if (inProgressItems.length > 0) {
        results.tasksUpdated = inProgressItems.length;

        // Replace unchecked boxes with checked boxes and add completion date
        inProgressItems.forEach(item => {
          const updatedItem = item.replace('- [ ]', `- [x]`) + ` (Completed: ${TODAY})`;
          content = content.replace(item, updatedItem);
        });

        // Move completed items to the Completed Consolidations section
        const completedSection = content.match(/## Completed Consolidations\s+([\s\S]*?)(?=##|$)/);

        if (completedSection) {
          // Extract the updated items with their completion dates
          const updatedItems = [];
          const inProgressSectionUpdated = content.match(/## In-Progress Consolidations\s+([\s\S]*?)(?=##|$)/);

          if (inProgressSectionUpdated && inProgressSectionUpdated[1]) {
            const matches = inProgressSectionUpdated[1].match(/- \[x\] (.*?)(?=\n- |\n\n|\n$|$)/g) || [];
            updatedItems.push(...matches);
          }

          // Append items to the Completed Consolidations section
          if (updatedItems.length > 0) {
            const newCompletedSection = completedSection[0].replace(
              completedSection[1],
              completedSection[1] + updatedItems.join('\n') + '\n\n'
            );
            content = content.replace(completedSection[0], newCompletedSection);

            // Clear the In-Progress section
            const clearedInProgressSection = '## In-Progress Consolidations\n\n*All planned consolidations completed.*\n\n';
            content = content.replace(inProgressSection[0], clearedInProgressSection);
          }
        }
      }
    }

    // 2. Update the progress metrics
    const progressMetricsSection = content.match(/## Progress Metrics\s+([\s\S]*?)(?=##|$)/);

    if (progressMetricsSection && progressMetricsSection[1]) {
      // Update overall progress to 100%
      let updatedMetricsSection = progressMetricsSection[1].replace(
        /- Overall Progress: \d+%/,
        '- Overall Progress: 100%'
      );

      // Count the number of completed consolidations
      const completedSection = content.match(/## Completed Consolidations\s+([\s\S]*?)(?=##|$)/);
      let completedCount = 0;

      if (completedSection && completedSection[1]) {
        const completedItems = completedSection[1].match(/- \[x\]/g) || [];
        completedCount = completedItems.length;
      }

      // Update consolidated files count
      updatedMetricsSection = updatedMetricsSection.replace(
        /- Consolidated Files: \d+/,
        `- Consolidated Files: ${completedCount}`
      );

      // Update the progress metrics section
      content = content.replace(progressMetricsSection[1], updatedMetricsSection);
      results.metricsUpdated = true;
    }

    // 3. Update the status summary
    const summarySection = content.match(/## Status Summary\s+([\s\S]*?)(?=##|$)/);

    if (summarySection && summarySection[1]) {
      const updatedSummarySection = summarySection[1].replace(
        /Status: In Progress/i,
        'Status: Completed'
      ).replace(
        /Estimated Completion: .*?(?=\n|\r|$)/i,
        `Completed: ${TODAY}`
      );

      content = content.replace(summarySection[1], updatedSummarySection);
      results.progressUpdated = true;
    }

    // Save the updated content if changes were made
    if (content !== originalContent) {
      await fs.promises.writeFile(PROGRESS_FILE, content, 'utf8');
      console.log(`Updated ${PROGRESS_FILE} successfully.`);
    } else {
      console.log('No changes needed in the progress document.');
    }

    return results;
  } catch (error) {
    console.error(`Error updating progress document: ${error.message}`);
    return results;
  }
}

/**
 * Generate a summary report of the updates
 */
function generateReport(results) {
  console.log('\n=== Consolidation Progress Update Report ===');
  console.log(`Tasks marked as completed: ${results.tasksUpdated}`);
  console.log(`Progress status updated: ${results.progressUpdated ? 'Yes' : 'No'}`);
  console.log(`Metrics updated: ${results.metricsUpdated ? 'Yes' : 'No'}`);
  console.log('\nNext steps:');
  console.log('1. Review the updated progress document');
  console.log('2. Commit the changes to the repository');
  console.log('3. Run the complete-docs-consolidation.sh script if not already done');
}

// Main execution
async function main() {
  try {
    console.log('Starting consolidation progress update...');
    const results = await updateProgressDocument();
    generateReport(results);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

main();
