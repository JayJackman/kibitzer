/**
 * Login page -- a form with username and password fields.
 *
 * Uses React Router v7's data patterns:
 * - <Form> instead of <form> -- React Router handles submission
 *   and calls the action defined in App.tsx (loginAction).
 * - useActionData() -- reads the return value from the action.
 *   If login failed, the action returns { error: "..." }.
 *   If login succeeded, the action returns a redirect (so this
 *   component never sees the success case).
 * - useNavigation() -- tells us if a form submission is in flight,
 *   so we can disable the button and show "Logging in...".
 *
 * The inputs are "uncontrolled" -- they have `name` attributes
 * instead of `value` + `onChange`. React Router reads the values
 * via native FormData when the form submits. This means no
 * useState for form fields.
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

export default function LoginPage() {
  // actionData is the return value from loginAction (defined in App.tsx).
  // It's undefined on first render, and { error: "..." } after a failed login.
  const actionData = useActionData() as { error: string } | undefined;

  // navigation.state is "submitting" while the action is running,
  // "idle" otherwise. This replaces the old useState(isSubmitting).
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Login</CardTitle>
          <CardDescription>
            Enter your credentials to access the bridge table.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/*
            <Form> from react-router (not the native <form>).
            method="post" tells React Router to call the route's action.
            The action reads form values via formData.get("username"), etc.
          */}
          <Form method="post" className="space-y-4">
            {/* Error message from the action (only shown after a failed login) */}
            {actionData?.error && (
              <div className="text-sm text-red-500">{actionData.error}</div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              {/*
                name="username" is how the action reads this value:
                formData.get("username"). No onChange needed.
              */}
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
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Logging in..." : "Log in"}
            </Button>

            <p className="text-center text-sm text-card-muted-foreground">
              {"Don't have an account? "}
              <Link to="/register" className="underline">
                Register
              </Link>
            </p>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
