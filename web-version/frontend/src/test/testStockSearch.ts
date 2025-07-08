/**
 * Test script for stock search service
 */
import { stockSearchService } from '../services/stockSearchService';

async function testStockSearch() {
  console.log('Testing Stock Search Service...\n');

  // Test 1: Get all stocks
  console.log('1. Fetching all stocks...');
  const start1 = Date.now();
  const allStocks1 = await stockSearchService.getAllStocks();
  const time1 = Date.now() - start1;
  console.log(`   - Total stocks: ${allStocks1.total}`);
  console.log(`   - Time taken: ${time1}ms`);
  console.log(`   - Sample: ${allStocks1.stocks.slice(0, 3).map(s => `${s.name} (${s.symbol})`).join(', ')}`);

  // Test 2: Get cached data (should be instant)
  console.log('\n2. Fetching cached data...');
  const start2 = Date.now();
  const allStocks2 = await stockSearchService.getAllStocks();
  const time2 = Date.now() - start2;
  console.log(`   - Time taken: ${time2}ms (should be < 10ms due to cache)`);
  console.log(`   - Cache working: ${time2 < 10 ? '✅' : '❌'}`);

  // Test 3: Search functionality
  console.log('\n3. Testing search...');
  const searchQueries = ['삼성', 'AAPL', '005930'];
  for (const query of searchQueries) {
    const results = stockSearchService.searchStocks(allStocks1.stocks, query);
    console.log(`   - Query "${query}": Found ${results.length} results`);
    if (results.length > 0) {
      console.log(`     First result: ${stockSearchService.formatStockDisplay(results[0])}`);
    }
  }

  // Test 4: Market-specific data
  console.log('\n4. Testing market-specific fetching...');
  const krStocks = await stockSearchService.getStocksByMarket('KR');
  const usStocks = await stockSearchService.getStocksByMarket('US');
  console.log(`   - Korean stocks: ${krStocks.total}`);
  console.log(`   - US stocks: ${usStocks.total}`);

  console.log('\n✅ All tests completed!');
}

// Run tests if this file is executed directly
if (require.main === module) {
  testStockSearch().catch(console.error);
}

export { testStockSearch };