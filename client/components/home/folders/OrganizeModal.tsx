"use client";

import React, { useState } from "react";
import { X } from "lucide-react";

interface OrganizeModalProps<T> {
  title: string; // e.g. "Organize Folders" or "Organize Quizzes"
  items: T[];
  onClose: () => void;
  onOrganized: (sorted: T[]) => void;
  renderItem: (item: T, index: number) => React.ReactNode;
}

function OrganizeModal<T>({
  title,
  items,
  onClose,
  onOrganized,
  renderItem,
}: OrganizeModalProps<T>) {
  const [sortedItems, setSortedItems] = useState<T[]>(items);

  const moveItem = (from: number, to: number) => {
    const updated = [...sortedItems];
    const [moved] = updated.splice(from, 1);
    updated.splice(to, 0, moved);
    setSortedItems(updated);
  };

  const handleSave = () => {
    onOrganized(sortedItems);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-navy-900">{title}</h2>
          <button onClick={onClose}>
            <X className="w-5 h-5 text-gray-500 hover:text-gray-700" />
          </button>
        </div>

        <div className="space-y-2">
          {sortedItems.map((item, index) => (
            <div
              key={index}
              className="flex justify-between items-center bg-gray-100 rounded-lg p-3"
            >
              {renderItem(item, index)}

              <div className="flex gap-2">
                <button
                  onClick={() =>
                    moveItem(index, index - 1 >= 0 ? index - 1 : index)
                  }
                  className="text-xs bg-gray-200 px-2 py-1 rounded"
                >
                  ↑
                </button>
                <button
                  onClick={() =>
                    moveItem(
                      index,
                      index + 1 < sortedItems.length ? index + 1 : index,
                    )
                  }
                  className="text-xs bg-gray-200 px-2 py-1 rounded"
                >
                  ↓
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-navy-900 text-white rounded-lg hover:bg-navy-800"
          >
            Save Order
          </button>
        </div>
      </div>
    </div>
  );
}

export default OrganizeModal;
