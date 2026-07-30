'use client';

import {
  IconArrowUp,
  IconCirclePlus,
  IconClipboard,
  IconClock,
  IconDatabaseSearch,
  IconLink,
  IconMathSymbols,
  IconPaperclip,
  IconPlus,
  IconSparkles,
  IconTemplate,
  IconX,
} from '@tabler/icons-react';
import Image from 'next/image';
import { useRef, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ModelPicker } from '@/components/model-picker';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface AttachedFile {
  id: string;
  name: string;
  file: File;
  preview?: string;
}

/**
 * Example prompts. Each one fills the input so the button is a real control
 * rather than decoration — every tool here maps to a tool the agent can call.
 */
const ACTIONS = [
  {
    id: 'calculator',
    icon: IconMathSymbols,
    label: 'Calculate',
    prompt: 'What is 1234 * 17?',
  },
  {
    id: 'time',
    icon: IconClock,
    label: 'Current time',
    prompt: 'What time is it in Bangkok right now?',
  },
  {
    id: 'knowledge',
    icon: IconDatabaseSearch,
    label: 'Search knowledge',
    prompt: 'When is the office closed?',
  },
  {
    id: 'combo',
    icon: IconSparkles,
    label: 'Multi-tool',
    prompt: 'What is 987 * 654, and what time is it in Tokyo?',
  },
];

export default function Ai04({
  onSubmit,
  model,
  onModelChange,
}: {
  onSubmit?: (prompt: string) => void;
  /** Selected model id, or "" to use the backend default */
  model: string;
  onModelChange: (model: string) => void;
}) {
  const [prompt, setPrompt] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const generateFileId = () => Math.random().toString(36).substring(7);
  const processFiles = (files: File[]) => {
    for (const file of files) {
      const fileId = generateFileId();
      const attachedFile: AttachedFile = {
        id: fileId,
        name: file.name,
        file,
      };

      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => {
          setAttachedFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, preview: reader.result as string } : f
            )
          );
        };
        reader.readAsDataURL(file);
      }

      setAttachedFiles((prev) => [...prev, attachedFile]);
    }
  };
  const submitPrompt = () => {
    if (prompt.trim() && onSubmit) {
      onSubmit(prompt.trim());
      setPrompt('');
    }
  };
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitPrompt();
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      processFiles(files);
    }
  };
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
  };
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitPrompt();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    processFiles(files);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = (fileId: string) => {
    setAttachedFiles((prev) => prev.filter((file) => file.id !== fileId));
  };

  return (
    <div className="mx-auto flex w-full flex-col gap-4">
      <h2 className="text-balance text-pretty text-center font-heading font-semibold text-2xl text-foreground tracking-tight sm:text-3xl">
        Ask the agent
      </h2>
      <p className="-my-3 text-balance pb-2 text-center text-muted-foreground text-sm">
        It picks its own tools — see exactly what each request costs in tokens
      </p>

      <div className="relative z-10 mx-auto flex w-full max-w-2xl flex-col content-center">
        <form
          className="overflow-visible rounded-xl border p-2 transition-colors duration-200 focus-within:border-ring"
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onSubmit={handleSubmit}
        >
          {attachedFiles.length > 0 && (
            <div className="relative mb-2 flex w-fit items-center gap-2 overflow-hidden">
              {attachedFiles.map((file) => (
                <Badge
                  className="group relative h-6 max-w-30 cursor-pointer overflow-hidden px-0 text-[13px] transition-colors hover:bg-accent"
                  key={file.id}
                  variant="outline"
                >
                  <span className="flex h-full items-center gap-1.5 overflow-hidden pl-1 font-normal">
                    <div className="relative flex h-4 min-w-4 items-center justify-center">
                      {file.preview ? (
                        <Image
                          alt={file.name}
                          className="absolute inset-0 h-4 w-4 rounded border object-cover"
                          height={16}
                          src={file.preview}
                          width={16}
                        />
                      ) : (
                        <IconPaperclip className="opacity-60" size={12} />
                      )}
                    </div>
                    <span className="inline overflow-hidden truncate pr-1.5">
                      {file.name}
                    </span>
                  </span>
                  <button
                    className="absolute right-1 z-10 rounded-sm p-0.5 text-muted-foreground opacity-0 focus-visible:bg-accent focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-background group-hover:opacity-100"
                    onClick={() => handleRemoveFile(file.id)}
                    type="button"
                  >
                    <IconX size={12} />
                  </button>
                </Badge>
              ))}
            </div>
          )}
          <Textarea
            className="max-h-50 min-h-12 resize-none rounded-none border-none bg-transparent! p-0 text-sm shadow-none focus-visible:border-transparent focus-visible:ring-0"
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            value={prompt}
          />

          <div className="flex items-center gap-1">
            <div className="flex items-end gap-0.5 sm:gap-1">
              <input
                className="sr-only"
                multiple
                onChange={handleFileSelect}
                ref={fileInputRef}
                type="file"
              />

              <DropdownMenu>
                <DropdownMenuTrigger
                  render={
                    <Button
                      aria-label="Add attachments"
                      className="ml-[-2px] rounded-md"
                      size="icon-sm"
                      type="button"
                      variant="ghost"
                    />
                  }
                >
                  <IconPlus size={16} />
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="start"
                  className="max-w-xs rounded-2xl p-1.5"
                >
                  <DropdownMenuGroup className="space-y-1">
                    <DropdownMenuItem
                      className="rounded-md text-xs"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <div className="flex items-center gap-2">
                        <IconPaperclip
                          className="text-muted-foreground"
                          size={16}
                        />
                        <span>Attach Files</span>
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem className="rounded-md text-xs">
                      <div className="flex items-center gap-2">
                        <IconLink className="text-muted-foreground" size={16} />
                        <span>Import from URL</span>
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem className="rounded-md text-xs">
                      <div className="flex items-center gap-2">
                        <IconClipboard
                          className="text-muted-foreground"
                          size={16}
                        />
                        <span>Paste from Clipboard</span>
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem className="rounded-md text-xs">
                      <div className="flex items-center gap-2">
                        <IconTemplate
                          className="text-muted-foreground"
                          size={16}
                        />
                        <span>Use Template</span>
                      </div>
                    </DropdownMenuItem>
                  </DropdownMenuGroup>
                </DropdownMenuContent>
              </DropdownMenu>

              {/*
                The block ships three decorative toggles here. Swapped for a
                real model picker so the control does something, and so the
                model being charged is visible right next to the send button.
              */}
              <ModelPicker onChange={onModelChange} value={model} />
            </div>

            <div className="ml-auto flex items-center gap-0.5 sm:gap-1">
              <Button
                aria-label="Send message"
                className="rounded-md"
                disabled={!prompt.trim()}
                size="icon-sm"
                type="submit"
                variant="default"
              >
                <IconArrowUp size={16} />
              </Button>
            </div>
          </div>

          <div
            className={cn(
              'pointer-events-none absolute inset-0 z-20 flex items-center justify-center rounded-[inherit] border border-border border-dashed bg-muted text-foreground text-sm transition-opacity duration-200',
              isDragOver ? 'opacity-100' : 'opacity-0'
            )}
          >
            <span className="flex w-full items-center justify-center gap-1 font-medium">
              <IconCirclePlus className="min-w-4" size={16} />
              Drop files here to add as attachments
            </span>
          </div>
        </form>
      </div>

      <div className="mx-auto flex min-h-0 max-w-250 shrink-0 flex-wrap items-center justify-center gap-3">
        {ACTIONS.map((action) => (
          <Button
            className="gap-2 rounded-full"
            key={action.id}
            onClick={() => setPrompt(action.prompt)}
            size="sm"
            type="button"
            variant="outline"
          >
            <action.icon size={16} />
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
