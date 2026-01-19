import { Product } from '../types';

/**
 * Sample product catalog for testing
 *
 * DO NOT MODIFY - This simulates a product database
 */
export const PRODUCTS: Product[] = [
  {
    id: 'prod_001',
    name: 'Wireless Mouse',
    price: 2999,  // $29.99
    description: 'Ergonomic wireless mouse with USB receiver'
  },
  {
    id: 'prod_002',
    name: 'Mechanical Keyboard',
    price: 8999,  // $89.99
    description: 'RGB mechanical keyboard with Cherry MX switches'
  },
  {
    id: 'prod_003',
    name: 'USB-C Hub',
    price: 4999,  // $49.99
    description: '7-in-1 USB-C hub with HDMI and SD card reader'
  },
  {
    id: 'prod_004',
    name: 'Webcam HD',
    price: 7999,  // $79.99
    description: '1080p HD webcam with built-in microphone'
  },
  {
    id: 'prod_005',
    name: 'Monitor Stand',
    price: 3499,  // $34.99
    description: 'Adjustable monitor stand with cable management'
  },
  {
    id: 'prod_006',
    name: 'Desk Lamp',
    price: 2499,  // $24.99
    description: 'LED desk lamp with adjustable brightness'
  },
  {
    id: 'prod_007',
    name: 'Laptop Sleeve',
    price: 1999,  // $19.99
    description: '15-inch padded laptop sleeve'
  },
  {
    id: 'prod_008',
    name: 'Wireless Charger',
    price: 2999,  // $29.99
    description: '15W fast wireless charging pad'
  },
  {
    id: 'prod_009',
    name: 'Headphone Stand',
    price: 1499,  // $14.99
    description: 'Aluminum headphone stand'
  },
  {
    id: 'prod_010',
    name: 'Cable Organizer',
    price: 999,   // $9.99
    description: 'Silicone cable organizer clips (set of 6)'
  },
  // This product will be used for "discontinued" testing
  {
    id: 'prod_discontinued',
    name: 'Legacy Adapter',
    price: 1999,
    description: 'This product is no longer available'
  }
];

export const PRODUCT_MAP = new Map<string, Product>(
  PRODUCTS.map(p => [p.id, p])
);
