# Composition patterns

How to keep a component's API from collapsing under variants. The chain is one
refactor, not four independent tips: remove the booleans, expose the parts,
define the context contract, lift the state into a provider.

Verified against: React 19.3.

## Contents

- `architecture-avoid-boolean-props` — the failure mode
- `patterns-explicit-variants` — one component per variant
- `architecture-compound-components` — expose the parts
- `state-context-interface` — the `{ state, actions, meta }` contract
- `state-decouple-implementation` — only the provider knows the source
- `state-lift-state` — reach state from outside the subtree
- `patterns-children-over-render-props` — and when render props win
- `react19-no-forwardref` — React 19 API changes

---

## `architecture-avoid-boolean-props` — the failure mode

Impact: CRITICAL for maintainability. Each boolean doubles the reachable state
space, and most combinations are meaningless — yet the conditionals inside the
component have to handle them.

```tsx
// Incorrect — 5 booleans, 32 nominal states, ~4 real ones
function Composer({ onSubmit, isThread, channelId, isDMThread, dmId, isEditing, isForwarding }) {
  return (
    <form>
      <Header />
      <Input />
      {isDMThread ? <AlsoSendToDMField id={dmId} />
        : isThread ? <AlsoSendToChannelField id={channelId} />
        : null}
      {isEditing ? <EditActions /> : isForwarding ? <ForwardActions /> : <DefaultActions />}
      <Footer onSubmit={onSubmit} />
    </form>
  )
}
```

A boolean prop is fine when it is genuinely orthogonal (`disabled`, `readOnly`,
`autoFocus`). It is the wrong tool when it *selects a variant* — when two
booleans are mutually exclusive, or when one gates whole branches of the tree.

---

## `patterns-explicit-variants` — one component per variant

Impact: MEDIUM, and it is what makes the call site readable.

```tsx
// Incorrect — what does this render?
<Composer isThread isEditing={false} channelId="abc" showAttachments showFormatting={false} />

// Correct
<ThreadComposer channelId="abc" />
<EditMessageComposer messageId="xyz" />
<ForwardMessageComposer messageId="123" />
```

Each variant states its own provider, its own pieces and its own actions. There
are no impossible states to reason about, and the variants still share every
internal part.

---

## `architecture-compound-components` — expose the parts

Impact: HIGH. Instead of a monolith with `renderX` props and `showY` flags,
publish the pieces and let the caller assemble them. Shared state travels
through context, not props.

```tsx
const ComposerContext = createContext<ComposerContextValue | null>(null)

function ComposerFrame({ children }: { children: React.ReactNode }) {
  return <form>{children}</form>
}

function ComposerInput() {
  const { state, actions, meta } = use(ComposerContext)
  return (
    <TextInput
      ref={meta.inputRef}
      value={state.input}
      onChange={(e) => actions.update((s) => ({ ...s, input: e.target.value }))}
    />
  )
}

export const Composer = {
  Provider: ComposerProvider,
  Frame: ComposerFrame,
  Input: ComposerInput,
  Submit: ComposerSubmit,
  Footer: ComposerFooter,
}
```

```tsx
<Composer.Provider state={state} actions={actions} meta={meta}>
  <Composer.Frame>
    <Composer.Input />
    <Composer.Footer>
      <Composer.Formatting />
      <Composer.Submit />
    </Composer.Footer>
  </Composer.Frame>
</Composer.Provider>
```

---

## `state-context-interface` — the `{ state, actions, meta }` contract

Impact: HIGH. Define the context as a generic interface with three parts, and
any provider can implement it. That is what makes the UI reusable across
use cases with completely different state implementations.

```tsx
interface ComposerState { input: string; attachments: Attachment[]; isSubmitting: boolean }
interface ComposerActions {
  update: (updater: (state: ComposerState) => ComposerState) => void
  submit: () => void
}
interface ComposerMeta { inputRef: React.RefObject<HTMLInputElement | null> }

interface ComposerContextValue {
  state: ComposerState
  actions: ComposerActions
  meta: ComposerMeta
}
```

- `state` — what is rendered.
- `actions` — what the user can do.
- `meta` — everything that is neither, most often refs.

UI components consume the interface. They never call a specific hook, so they
work with any provider that satisfies it.

---

## `state-decouple-implementation` — only the provider knows the source

Impact: MEDIUM. The provider is the single place that knows whether state comes
from `useState`, a global store, or a server sync.

```tsx
// Local state for an ephemeral form
function ForwardMessageProvider({ children }) {
  const [state, setState] = useState(initialState)
  const submit = useForwardMessage()
  return <Composer.Provider state={state} actions={{ update: setState, submit }}>{children}</Composer.Provider>
}

// Globally synced state for a channel — same UI, different provider
function ChannelProvider({ channelId, children }) {
  const { state, update, submit } = useGlobalChannel(channelId)
  return <Composer.Provider state={state} actions={{ update, submit }}>{children}</Composer.Provider>
}
```

---

## `state-lift-state` — reach state from outside the subtree

Impact: HIGH. State held inside a component is unreachable from its siblings.
The two usual workarounds are both worse than lifting it.

```tsx
// Incorrect — syncing upward through an effect, on every keystroke
function Dialog() {
  const [input, setInput] = useState('')
  return (<><Composer onInputChange={setInput} /><Preview input={input} /></>)
}

// Incorrect — reading state out of a ref at submit time
<Composer stateRef={stateRef} />
<ForwardButton onPress={() => submit(stateRef.current)} />

// Correct — the provider wraps everything that needs the state
function ForwardMessageDialog() {
  return (
    <ForwardMessageProvider>
      <Dialog>
        <ForwardMessageComposer />
        <MessagePreview />
        <DialogActions>
          <CancelButton />
          <ForwardButton />
        </DialogActions>
      </Dialog>
    </ForwardMessageProvider>
  )
}
```

---

## `patterns-children-over-render-props`

Impact: MEDIUM. `children` composes naturally and needs no callback signature;
`renderHeader` / `renderFooter` / `renderActions` props do not.

```tsx
// Incorrect
<Composer renderHeader={() => <CustomHeader />} renderActions={() => <SubmitButton />} />

// Correct
<Composer.Frame>
  <CustomHeader />
  <Composer.Input />
  <Composer.Footer><SubmitButton /></Composer.Footer>
</Composer.Frame>
```

Render props are still right when the parent must hand data *back* to the child
— a list rendering each item:

```tsx
<List data={items} renderItem={({ item, index }) => <Item item={item} index={index} />} />
```

Children for static structure; render props for data flowing back.

---

## `react19-no-forwardref` — React 19 API changes

Impact: MEDIUM. Two API changes remove boilerplate (React 19+):

```tsx
// Old — forwardRef wrapper
const Input = forwardRef<HTMLInputElement, Props>((props, ref) => <input ref={ref} {...props} />)

// Current — ref is an ordinary prop
function Input({ ref, ...props }: Props & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />
}
```

```tsx
// Old
const value = useContext(MyContext)
// Current
const value = use(MyContext)
```

`use()` may also be called conditionally, which `useContext` could not. On React
18 and earlier both old forms remain correct — check the `react` version before
rewriting.

<!-- sources: vercel-react-bp, react-docs -->
