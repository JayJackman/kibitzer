/**
 * Registration page -- create a new account.
 *
 * Same React Router v7 patterns as Login:
 * - <Form> submits to the registerAction defined in App.tsx
 * - useActionData() reads errors from the action
 * - useNavigation() tracks submission state
 * - Uncontrolled inputs with `name` attributes (no useState)
 *
 * Password confirmation is validated in the action (not here).
 * The action checks that "password" and "confirmPassword" match
 * before calling the API.
 */
import { Form, Link, useActionData, useNavigation } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const actionData = useActionData() as { error: string } | undefined;
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Register</CardTitle>
          <CardDescription>
            Create an account to start playing bridge.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form method="post" className="space-y-4">
            {actionData?.error && (
              <div className="text-sm text-red-500">{actionData.error}</div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                minLength={6}
              />
              <p className="text-xs text-card-muted-foreground">
                Must be at least 6 characters.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              {/*
                name="confirmPassword" -- the registerAction reads this
                to verify it matches the password field.
              */}
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Creating account..." : "Create account"}
            </Button>

            <p className="text-center text-sm text-card-muted-foreground">
              Already have an account?{" "}
              <Link to="/login" className="underline">
                Log in
              </Link>
            </p>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
