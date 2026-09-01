"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

type NavLinkProps = Omit<ComponentProps<typeof Link>, "href"> & {
  href: string;
  /** casa apenas o pathname idêntico (por padrão também casa sub-rotas) */
  exact?: boolean;
  /** classe extra aplicada só quando ativo */
  activeClassName?: string;
};

export function NavLink({
  href,
  exact = false,
  className,
  activeClassName,
  children,
  ...props
}: NavLinkProps) {
  const pathname = usePathname() || "";
  const active = exact
    ? pathname === href
    : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      data-active={active ? "" : undefined}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent/60 hover:text-foreground",
        active && cn("bg-accent font-medium text-accent-foreground hover:text-accent-foreground", activeClassName),
        className,
      )}
      {...props}
    >
      {children}
    </Link>
  );
}
