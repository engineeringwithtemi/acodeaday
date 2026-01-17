import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import type { TestCase } from '../types/api'

interface CustomTestCase {
  id: string
  input: string
  isCustom: true
}

interface TestCasesPanelProps {
  testCases: TestCase[]
  onCustomTestCasesChange?: (customInputs: any[][]) => void
}

export function TestCasesPanel({ testCases, onCustomTestCasesChange }: TestCasesPanelProps) {
  // Only show first 3 test cases
  const visibleTestCases = testCases.slice(0, 3)

  const [activeTab, setActiveTab] = useState(0)
  const [customTestCases, setCustomTestCases] = useState<CustomTestCase[]>([])


  const addCustomTestCase = () => {
    const newCase: CustomTestCase = {
      id: `custom-${Date.now()}`,
      input: '[]',
      isCustom: true,
    }
    const updated = [...customTestCases, newCase]
    setCustomTestCases(updated)
    setActiveTab(visibleTestCases.length + updated.length - 1)
    notifyCustomInputsChange(updated)
  }

  const removeCustomTestCase = (index: number) => {
    const updated = customTestCases.filter((_, i) => i !== index)
    setCustomTestCases(updated)
    // Adjust active tab if needed
    if (activeTab >= visibleTestCases.length + index) {
      setActiveTab(Math.max(0, activeTab - 1))
    }
    notifyCustomInputsChange(updated)
  }

  const updateCustomTestCase = (index: number, input: string) => {
    const updated = customTestCases.map((tc, i) =>
      i === index ? { ...tc, input } : tc
    )
    setCustomTestCases(updated)
    notifyCustomInputsChange(updated)
  }

  const notifyCustomInputsChange = (cases: CustomTestCase[]) => {
    if (onCustomTestCasesChange) {
      const customInputs = cases.map(tc => {
        try {
          return JSON.parse(tc.input)
        } catch {
          return null
        }
      }).filter(Boolean)
      onCustomTestCasesChange(customInputs)
    }
  }

  const isCustomTab = activeTab >= visibleTestCases.length
  const customIndex = activeTab - visibleTestCases.length

  return (
    <div className="h-full flex flex-col bg-gray-800">
      {/* Tab Header */}
      <div className="flex items-center border-b border-gray-700 bg-gray-800 px-2 overflow-x-auto">
        {visibleTestCases.map((_, index) => (
          <button
            key={`case-${index}`}
            onClick={() => setActiveTab(index)}
            className={`px-3 py-2 text-xs font-semibold whitespace-nowrap transition-colors ${
              activeTab === index
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Case {index + 1}
          </button>
        ))}

        {customTestCases.map((tc, index) => (
          <div key={tc.id} className="relative flex items-center">
            <button
              onClick={() => setActiveTab(visibleTestCases.length + index)}
              className={`px-3 py-2 text-xs font-semibold whitespace-nowrap transition-colors ${
                activeTab === visibleTestCases.length + index
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Case {visibleTestCases.length + index + 1}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                removeCustomTestCase(index)
              }}
              className="p-1 text-gray-500 hover:text-red-400 transition-colors"
            >
              <X size={12} />
            </button>
          </div>
        ))}

        <button
          onClick={addCustomTestCase}
          className="px-2 py-2 text-gray-500 hover:text-cyan-400 transition-colors"
          title="Add custom test case"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!isCustomTab && visibleTestCases[activeTab] && (
          <TestCaseDisplay testCase={visibleTestCases[activeTab]} />
        )}

        {isCustomTab && customTestCases[customIndex] && (
          <CustomTestCaseEditor
            value={customTestCases[customIndex].input}
            onChange={(input) => updateCustomTestCase(customIndex, input)}
          />
        )}
      </div>
    </div>
  )
}

function TestCaseDisplay({ testCase }: { testCase: TestCase }) {
  const formatValue = (value: any): string => {
    return JSON.stringify(value)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-2">Input</label>
        <pre className="p-3 bg-gray-900 rounded-lg text-sm text-cyan-400 font-mono overflow-x-auto">
          {formatValue(testCase.input)}
        </pre>
      </div>
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-2">Expected Output</label>
        <pre className="p-3 bg-gray-900 rounded-lg text-sm text-green-400 font-mono overflow-x-auto">
          {formatValue(testCase.expected)}
        </pre>
      </div>
    </div>
  )
}

function CustomTestCaseEditor({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [error, setError] = useState<string | null>(null)

  const handleChange = (newValue: string) => {
    onChange(newValue)
    try {
      JSON.parse(newValue)
      setError(null)
    } catch (e) {
      setError('Invalid JSON format')
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-2">
          Custom Input (JSON array of arguments)
        </label>
        <textarea
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          className={`w-full h-32 p-3 bg-gray-900 rounded-lg text-sm text-cyan-400 font-mono resize-none focus:outline-none focus:ring-2 ${
            error ? 'ring-red-500' : 'focus:ring-cyan-500'
          }`}
          placeholder='e.g., [[1, 2, 3], 6]'
        />
        {error && (
          <p className="mt-1 text-xs text-red-400">{error}</p>
        )}
        <p className="mt-2 text-xs text-gray-500">
          Enter arguments as a JSON array. For example, for twoSum(nums, target), use: [[2,7,11,15], 9]
        </p>
      </div>
    </div>
  )
}
