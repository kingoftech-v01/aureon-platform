/**
 * Keyboard Shortcuts Modal Component
 * Aureon by Rhematek Solutions
 *
 * Displays all available keyboard shortcuts organized by section
 */

import React from 'react';
import Modal, { ModalHeader, ModalBody } from './Modal';

interface KeyboardShortcutsProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ShortcutItem {
  keys: string[];
  description: string;
}

interface ShortcutSection {
  title: string;
  shortcuts: ShortcutItem[];
}

const sections: ShortcutSection[] = [
  {
    title: 'Navigation',
    shortcuts: [
      { keys: ['G', 'then', 'D'], description: 'Go to Dashboard' },
      { keys: ['G', 'then', 'C'], description: 'Go to Clients' },
      { keys: ['G', 'then', 'I'], description: 'Go to Invoices' },
      { keys: ['G', 'then', 'P'], description: 'Go to Payments' },
      { keys: ['G', 'then', 'A'], description: 'Go to Analytics' },
    ],
  },
  {
    title: 'Create',
    shortcuts: [
      { keys: ['N', 'then', 'I'], description: 'New Invoice' },
      { keys: ['N', 'then', 'C'], description: 'New Client' },
    ],
  },
  {
    title: 'General',
    shortcuts: [
      { keys: ['Ctrl', 'K'], description: 'Search' },
      { keys: ['?'], description: 'Show shortcuts' },
      { keys: ['Esc'], description: 'Close modal' },
    ],
  },
];

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({ isOpen, onClose }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalHeader>Keyboard Shortcuts</ModalHeader>
      <ModalBody>
        <div className="space-y-6">
          {sections.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                {section.title}
              </h3>
              <div className="space-y-2">
                {section.shortcuts.map((shortcut, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <div className="flex items-center space-x-1">
                      {shortcut.keys.map((key, keyIdx) => (
                        <React.Fragment key={keyIdx}>
                          {key === 'then' ? (
                            <span className="text-xs text-gray-400 dark:text-gray-500 mx-1">
                              then
                            </span>
                          ) : (
                            <kbd className="inline-flex items-center justify-center min-w-[28px] px-2 py-1 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded shadow-sm">
                              {key}
                            </kbd>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Press <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">Esc</kbd> to close
          </p>
        </div>
      </ModalBody>
    </Modal>
  );
};

export default KeyboardShortcuts;
