"use client";

interface FoodBoxProps {
  data: {
    eatOutside?: string;
    dietary?: string;
    meals?: string[];
    [key: string]: any;  // Allow additional form fields
  };
}

export default function FoodBox({ data }: FoodBoxProps) {
  if (data.eatOutside === 'no') return null;

  return (
    <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10 mb-6">
      <h3 className="text-orange-400 font-mono font-bold uppercase text-sm mb-4">
        🍴 Foodie Recommendations
      </h3>
      <div className="space-y-2">
        <p className="text-sm font-medium text-white/70">
          Profile: <span className="capitalize font-bold text-orange-400">{data.dietary || 'Standard'}</span>
        </p>
        {data.meals && data.meals.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {data.meals.map((meal: string) => (
              <span key={meal} className="bg-orange-500/20 text-orange-400 text-xs px-3 py-1 rounded-full font-bold border border-orange-500/30">
                {meal}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
