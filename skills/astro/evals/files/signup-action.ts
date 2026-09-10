// Original path in the project: src/actions/index.ts
import { defineAction } from "astro:actions";
import { z } from "astro:content";
import { createAccount } from "../lib/accounts";

export const server = {
  signup: defineAction({
    input: z.object({
      email: z.string().email(),
      plan: z.enum(["free", "pro"]),
      terms: z.boolean(),
      avatar: z.instanceof(File).optional(),
    }),
    handler: async (input) => {
      const account = await createAccount(input);
      return { id: account.id };
    },
  }),
};
