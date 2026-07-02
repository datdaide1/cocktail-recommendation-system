"use client";

import React, { useState } from "react";
import Image from "next/image";
import { BlockRenderer } from "../components/sdui/BlockRegistry";
import { Block } from "../components/sdui/types";

// Mock data matching the schemas for B2C User Mode
const b2cBlocks: Block[] = [
  {
    type: 'text',
    content: 'Chào mừng bạn đến với The Mixologist B2C. Khám phá các địa điểm sôi động và cocktail độc đáo được cá nhân hóa cho bạn.',
  },
  {
    type: 'carousel_venues',
    data: [
      {
        id: 'venue-c1',
        name: 'The Rabbit Hole',
        vibe: 'Cozy Lounge',
        vibe_tags: ['Classic', 'Speakeasy', 'Jazz'],
        rationale: 'Không gian ấm cúng dưới lòng đất thích hợp cho trò chuyện riêng tư.',
      },
      {
        id: 'venue-c2',
        name: 'Firkin Bar',
        vibe: 'Premium Whiskey',
        vibe_tags: ['Luxury', 'Bespoke', 'Quiet'],
        rationale: 'Nổi tiếng với dịch vụ cocktail thiết kế riêng theo tâm trạng.',
      },
    ],
  },
  {
    type: 'carousel_cocktails',
    data: [
      {
        id: 'cocktail-c1',
        name: 'Classic Manhattan',
        alcoholic_type: 'Alcoholic',
        base_liquor: 'Rye Whiskey',
        rationale: 'Sự kết hợp nồng nàn giữa Rye Whiskey và Vermouth ngọt ngào.',
      },
      {
        id: 'cocktail-c2',
        name: 'Espresso Martini',
        alcoholic_type: 'Alcoholic',
        base_liquor: 'Vodka',
        rationale: 'Cung cấp năng lượng tinh tế từ hạt cà phê chất lượng cao.',
      },
    ],
  },
  {
    type: 'rationale',
    content: 'Đề xuất dựa trên sở thích uống rượu nền Whiskey và mong muốn không gian yên tĩnh của bạn.',
  },
  {
    type: 'quick_replies',
    actions: ['Tìm Quán Bar Khác', 'Đổi Sang Vị Chua Ngọt', 'Xem Ưu Đãi Gần Đây'],
  },
];

// Mock data matching the schemas for B2B Merchant Mode
const b2bBlocks: Block[] = [
  {
    type: 'text',
    content: 'Hệ thống quản trị The Mixologist B2B. Xem phân tích xu hướng đồ uống phổ biến và đề xuất điều chỉnh thực đơn tối ưu hóa doanh thu.',
  },
  {
    type: 'carousel_venues',
    data: [
      {
        id: 'venue-b1',
        name: 'Layla Eatery & Bar',
        vibe: 'Lively Bar',
        vibe_tags: ['Cocktails', 'Social', 'Crowded'],
        rationale: 'Địa điểm thu hút lượng khách hàng trẻ tuổi cao nhất khu vực.',
      },
      {
        id: 'venue-b2',
        name: 'Summer Experiment',
        vibe: 'Creative Hub',
        vibe_tags: ['Modern Craft', 'Experimental'],
        rationale: 'Đón đầu xu hướng đồ uống sáng tạo của giới trẻ thành thị.',
      },
    ],
  },
  {
    type: 'carousel_cocktails',
    data: [
      {
        id: 'cocktail-b1',
        name: 'Classic Negroni',
        alcoholic_type: 'Alcoholic',
        base_liquor: 'Gin',
        rationale: 'Đồ uống đứng đầu về tỉ lệ quay lại của khách hàng trung niên.',
      },
      {
        id: 'cocktail-b2',
        name: 'Whiskey Sour',
        alcoholic_type: 'Alcoholic',
        base_liquor: 'Bourbon',
        rationale: 'Món cocktail mang lại biên lợi nhuận cao nhất trong quý này.',
      },
    ],
  },
  {
    type: 'rationale',
    content: 'Gợi ý từ thuật toán dự báo xu hướng thị trường mùa hè 2026.',
  },
  {
    type: 'quick_replies',
    actions: ['Tải Báo Cáo Doanh Thu', 'Cập Nhật Thực Đơn', 'Xem Phản Hồi Khách Hàng'],
  },
];

export default function Home() {
  const [actionLog, setActionLog] = useState<string>("Chưa có thao tác nào.");

  const handleAction = (mode: 'B2C' | 'B2B', actionType: string, payload: unknown) => {
    const time = new Date().toLocaleTimeString();
    setActionLog(`[${time}] [${mode}] Thao tác: "${actionType}" | Dữ liệu: ${JSON.stringify(payload)}`);
  };

  return (
    <div className="min-h-screen bg-bg-deepest text-text-primary p-6 md:p-12 flex flex-col gap-8">
      {/* Page Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-border-default pb-6 gap-4">
        <div>
          <h1 className="text-h1 font-bold tracking-tight text-left">
            SDUI Components Showcase
          </h1>
          <p className="text-body-sm text-text-secondary text-left mt-1">
            Midnight Lounge Server-Driven UI Demonstration
          </p>
        </div>
        <Image
          className="opacity-80"
          src="/next.svg"
          alt="Next.js logo"
          width={90}
          height={18}
          priority
        />
      </header>

      {/* Interactive Action Log Panel */}
      <div className="bg-bg-elevated border border-[var(--mode-accent,rgba(255,255,255,0.1))] rounded-xl p-4 transition-all duration-300">
        <h3 className="text-h3 font-semibold text-left mb-2 flex items-center gap-2">
          <span>⚡</span> Nhật ký Hoạt động (State Log)
        </h3>
        <p className="text-data-sm text-left font-mono bg-bg-surface p-3 rounded-lg border border-border-subtle break-all">
          {actionLog}
        </p>
      </div>

      {/* Main Grid: B2C vs B2B Modes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* B2C User Mode Section */}
        <section 
          data-mode="b2c" 
          className="flex flex-col gap-6 bg-bg-elevated border border-border-subtle rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden"
        >
          {/* Neon blue background glow */}
          <div className="absolute top-0 right-0 w-48 h-48 bg-secondary-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex items-center gap-3 border-b border-border-subtle pb-4">
            <span className="text-overline tracking-widest text-[var(--mode-accent)] font-semibold font-body">
              B2C MODE — USER INTERFACE
            </span>
            <div className="h-2.5 w-2.5 rounded-full bg-[var(--mode-accent)] animate-pulse" />
          </div>

          <div className="flex flex-col gap-6">
            {b2cBlocks.map((block, idx) => (
              <div key={idx} className="flex flex-col gap-2">
                <span className="text-micro text-text-tertiary uppercase tracking-wider">
                  Block type: {block.type}
                </span>
                <BlockRenderer 
                  block={block} 
                  onAction={(actionType, payload) => handleAction('B2C', actionType, payload)}
                />
              </div>
            ))}
          </div>
        </section>

        {/* B2B Merchant Mode Section */}
        <section 
          data-mode="b2b" 
          className="flex flex-col gap-6 bg-bg-elevated border border-border-subtle rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden"
        >
          {/* Amber gold background glow */}
          <div className="absolute top-0 right-0 w-48 h-48 bg-primary-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center gap-3 border-b border-border-subtle pb-4">
            <span className="text-overline tracking-widest text-[var(--mode-accent)] font-semibold font-body">
              B2B MODE — MERCHANT DASHBOARD
            </span>
            <div className="h-2.5 w-2.5 rounded-full bg-[var(--mode-accent)] animate-pulse" />
          </div>

          <div className="flex flex-col gap-6">
            {b2bBlocks.map((block, idx) => (
              <div key={idx} className="flex flex-col gap-2">
                <span className="text-micro text-text-tertiary uppercase tracking-wider">
                  Block type: {block.type}
                </span>
                <BlockRenderer 
                  block={block} 
                  onAction={(actionType, payload) => handleAction('B2B', actionType, payload)}
                />
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
}
