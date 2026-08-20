import { Slot } from "@radix-ui/react-slot";
import {
  createContext,
  type ComponentProps,
  type HTMLAttributes,
  type PropsWithChildren,
  useContext,
  useId,
} from "react";
import {
  Controller,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
  FormProvider,
  useFormContext,
} from "react-hook-form";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const Form = FormProvider;
const FieldContext = createContext<{ name: string }>({ name: "" });
const ItemContext = createContext<{ id: string }>({ id: "" });

export function FormField<T extends FieldValues, N extends FieldPath<T>>(
  props: ControllerProps<T, N>,
) {
  return (
    <FieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FieldContext.Provider>
  );
}
export function FormItem({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  const id = useId();
  return (
    <ItemContext.Provider value={{ id }}>
      <div className={cn("space-y-2", className)} {...props} />
    </ItemContext.Provider>
  );
}
function useFormField() {
  const field = useContext(FieldContext);
  const item = useContext(ItemContext);
  const { getFieldState, formState } = useFormContext();
  return {
    ...getFieldState(field.name, formState),
    id: item.id,
    name: field.name,
  };
}
export function FormLabel(props: ComponentProps<typeof Label>) {
  const field = useFormField();
  return (
    <Label
      htmlFor={`${field.id}-control`}
      className={cn(field.error && "text-destructive", props.className)}
      {...props}
    />
  );
}
export function FormControl(props: PropsWithChildren) {
  const field = useFormField();
  return (
    <Slot
      id={`${field.id}-control`}
      aria-invalid={Boolean(field.error)}
      aria-describedby={`${field.id}-message`}
      {...props}
    />
  );
}
export function FormMessage({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  const field = useFormField();
  const body = field.error?.message ? String(field.error.message) : children;
  return body ? (
    <p
      id={`${field.id}-message`}
      className={cn("text-sm text-destructive", className)}
      {...props}
    >
      {body}
    </p>
  ) : null;
}
