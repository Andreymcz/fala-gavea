import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-blue-600 text-white",
        secondary: "border-transparent bg-gray-100 text-gray-900",
        destructive: "border-transparent bg-red-600 text-white",
        outline: "text-gray-900",
        // Urgency variants
        "urgency-alta": "border-transparent bg-[#E53E3E] text-white",
        "urgency-media": "border-transparent bg-[#DD6B20] text-white",
        "urgency-baixa": "border-transparent bg-[#3182CE] text-white",
        // Status variants
        "status-pendente": "border-transparent bg-gray-200 text-gray-700",
        "status-em_analise": "border-transparent bg-yellow-100 text-yellow-800",
        "status-encaminhado": "border-transparent bg-blue-100 text-blue-800",
        "status-resolvido": "border-transparent bg-green-100 text-green-800",
        // Forwarding status variants
        "fwd-aguardando_solucao": "border-transparent bg-orange-100 text-orange-800",
        "fwd-solucao_em_andamento": "border-transparent bg-blue-100 text-blue-800",
        "fwd-finalizado": "border-transparent bg-green-100 text-green-800",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
