import { defineStore } from 'pinia'
import { ref } from 'vue'
import { testsApi, type TestCaseData, type TestRunResult, type TestStepData } from '../api/tests'

export const useTestStore = defineStore('tests', () => {
  const testCases = ref<Record<string, TestCaseData>>({})
  const runResults = ref<Record<string, TestRunResult>>({})
  const editingCase = ref<TestCaseData | null>(null)

  async function loadTests() {
    const res = await testsApi.list()
    testCases.value = res.test_cases
  }

  async function createTest(data: any) {
    const tc = await testsApi.create(data)
    testCases.value[tc.id] = tc
    return tc
  }

  async function updateTest(id: string, data: any) {
    const tc = await testsApi.update(id, data)
    testCases.value[id] = tc
    return tc
  }

  async function deleteTest(id: string) {
    await testsApi.delete(id)
    delete testCases.value[id]
    delete runResults.value[id]
  }

  async function runTest(id: string) {
    const result = await testsApi.run(id)
    runResults.value[id] = result
    return result
  }

  async function recordFromHistory() {
    return await testsApi.record()
  }

  function setEditing(tc: TestCaseData | null) {
    editingCase.value = tc
  }

  return {
    testCases,
    runResults,
    editingCase,
    loadTests,
    createTest,
    updateTest,
    deleteTest,
    runTest,
    recordFromHistory,
    setEditing,
  }
})
