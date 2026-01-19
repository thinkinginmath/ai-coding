// Test setup file
// This runs before each test file

import { store } from './index';

beforeEach(() => {
  // Clear store between tests
  store.clear();
});
