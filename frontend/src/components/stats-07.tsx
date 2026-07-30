'use client';

import { PolarAngleAxis, RadialBar, RadialBarChart } from 'recharts';
import { Card, CardContent } from '@/components/ui/card';
import { type ChartConfig, ChartContainer } from '@/components/ui/chart';

export interface Stat07Item {
  /** Row label, e.g. "Prompt tokens" */
  name: string;
  /** Ring fill percentage, 0-100 */
  capacity: number;
  /** Current value (already formatted-friendly number) */
  current: number;
  /** Total the current value is measured against */
  allowed: number;
  /** Unit shown after the numbers, e.g. "tokens" */
  unit?: string;
  fill?: string;
}

const chartConfig = {
  capacity: {
    label: 'Capacity',
    color: 'hsl(var(--primary))',
  },
} satisfies ChartConfig;

const fmt = (n: number) => Math.round(n).toLocaleString();

export default function Stats07({
  title,
  description,
  items,
}: {
  title: string;
  description?: React.ReactNode;
  items: Stat07Item[];
}) {
  return (
    <div className="w-full">
      <h2 className="text-balance font-medium text-foreground text-xl">
        {title}
      </h2>
      {description && (
        <p className="mt-1 text-pretty text-muted-foreground text-sm leading-6">
          {description}
        </p>
      )}
      <dl className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <Card className="p-4 shadow-2xs" key={item.name}>
            <CardContent className="flex items-center space-x-4 p-0">
              <div className="relative flex items-center justify-center">
                <ChartContainer
                  className="h-[80px] w-[80px]"
                  config={chartConfig}
                >
                  {/*
                    The block ships innerRadius/outerRadius 30/60, but the ring
                    lives in an 80px box (max radius 40) so recharts 3 clipped
                    the value bar away and only the grey track showed. Percent
                    radii keep it inside the box at any size.
                  */}
                  <RadialBarChart
                    barSize={6}
                    data={[item]}
                    endAngle={-270}
                    innerRadius="72%"
                    outerRadius="100%"
                    startAngle={90}
                  >
                    <PolarAngleAxis
                      angleAxisId={0}
                      axisLine={false}
                      domain={[0, 100]}
                      tick={false}
                      type="number"
                    />
                    <RadialBar
                      angleAxisId={0}
                      background
                      cornerRadius={10}
                      dataKey="capacity"
                      fill={item.fill ?? 'var(--primary)'}
                      isAnimationActive={false}
                    />
                  </RadialBarChart>
                </ChartContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="font-medium font-mono text-base text-foreground tabular-nums">
                    {Math.round(item.capacity)}%
                  </span>
                </div>
              </div>
              <div className="min-w-0">
                <dt className="truncate font-medium text-foreground text-sm">
                  {item.name}
                </dt>
                <dd className="font-mono text-muted-foreground text-sm tabular-nums">
                  {fmt(item.current)} of {fmt(item.allowed)}
                  {item.unit ? ` ${item.unit}` : ''}
                </dd>
              </div>
            </CardContent>
          </Card>
        ))}
      </dl>
    </div>
  );
}
