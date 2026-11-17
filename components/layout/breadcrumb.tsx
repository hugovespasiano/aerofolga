"use client";

import { ChevronRight, Home } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment } from "react";

export function Breadcrumb() {
  const pathname = usePathname();
  const paths = pathname.split("/").filter(Boolean);

  if (paths.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="mb-4 flex items-center text-sm text-muted-foreground">
      <Link href="/" className="hover:text-foreground transition-colors flex items-center gap-1">
        <Home className="h-4 w-4" />
        <span className="sr-only">Home</span>
      </Link>
      
      {paths.map((path, index) => {
        const href = `/${paths.slice(0, index + 1).join("/")}`;
        const isLast = index === paths.length - 1;
        const formattedPath = path.charAt(0).toUpperCase() + path.slice(1).replace(/-/g, " ");

        return (
          <Fragment key={path}>
            <ChevronRight className="h-4 w-4 mx-1" />
            {isLast ? (
              <span className="font-medium text-foreground" aria-current="page">
                {formattedPath}
              </span>
            ) : (
              <Link href={href} className="hover:text-foreground transition-colors">
                {formattedPath}
              </Link>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
