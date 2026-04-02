import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, UploadCloud, CheckCircle, FileText, Calendar, DollarSign, XCircle, ArrowRight, Loader2, RefreshCcw, LayoutDashboard, Settings } from "lucide-react";

export default function App() {
  const [userId, setUserId] = useState("default_user");
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Auto clean file input
  useEffect(() => {
    if (!selectedFile && document.getElementById("file-upload")) {
      document.getElementById("file-upload").value = "";
    }
  }, [selectedFile]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".csv")) {
        setSelectedFile(file);
      } else {
        alert("Please upload a valid CSV file.");
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      setLoading(true);

      const res = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        headers: { "X-User-ID": userId },
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Failed to process file on server.");
      }

      const data = await res.json();
      console.log("API Response:", data);

      setEmails(Array.isArray(data) ? data : data.emails || []);
    } catch (error) {
      console.error("Error:", error);
      alert("Backend error! Check Flask server.");
    } finally {
      setLoading(false);
      setSelectedFile(null); // Reset selection
    }
  };

  const handleFetchGmail = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:5000/fetch-emails", {
        method: "GET",
        headers: { "X-User-ID": userId },
      });

      if (!res.ok) {
        throw new Error("Failed to fetch from Gmail API.");
      }

      const data = await res.json();
      console.log("Gmail API Response:", data);

      setEmails(Array.isArray(data) ? data : data.emails || []);
    } catch (error) {
      console.error("Error:", error);
      alert("Backend error! Check Flask server and ensure credentials.json is valid.");
    } finally {
      setLoading(false);
    }
  };

  const handleHITL = async (threadId, action, feedback = null) => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:5000/approve", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId
        },
        body: JSON.stringify({ thread_id: threadId, action, feedback }),
      });

      if (!res.ok) throw new Error("Approval failed");

      const updated = await res.json();

      // Update local state for that specific email
      setEmails(prev => prev.map(e =>
        e.thread_id === threadId
          ? { ...e, Agent_Action: updated.Agent_Action || "Action processed." }
          : e
      ));
    } catch (error) {
      console.error("HITL Error:", error);
      alert("Error processing approval.");
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category) => {
    const cat = category?.toLowerCase() || "";
    if (cat.includes("work")) return <Calendar className="w-5 h-5 text-blue-400" />;
    if (cat.includes("finance")) return <DollarSign className="w-5 h-5 text-emerald-400" />;
    if (cat.includes("personal")) return <CheckCircle className="w-5 h-5 text-purple-400" />;
    if (cat.includes("travel")) return <UploadCloud className="w-5 h-5 text-amber-400" rotate={90} />;
    if (cat.includes("social")) return <RefreshCcw className="w-5 h-5 text-pink-400" />;
    if (cat.includes("ignore")) return <XCircle className="w-5 h-5 text-slate-500" />;
    if (cat.includes("notify")) return <Mail className="w-5 h-5 text-orange-400" />;
    return <Mail className="w-5 h-5 text-slate-400" />;
  };

  const getCategoryColor = (category) => {
    const cat = category?.toLowerCase() || "";
    if (cat.includes("work")) return "bg-blue-500/10 text-blue-500 border-blue-500/20";
    if (cat.includes("finance")) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    if (cat.includes("personal")) return "bg-purple-500/10 text-purple-500 border-purple-500/20";
    if (cat.includes("travel")) return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    if (cat.includes("social")) return "bg-pink-500/10 text-pink-500 border-pink-500/20";
    if (cat.includes("ignore")) return "bg-slate-500/10 text-slate-500 border-slate-500/20";
    if (cat.includes("notify")) return "bg-orange-500/10 text-orange-500 border-orange-500/20";
    return "bg-slate-500/10 text-slate-500 border-slate-500/20";
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-slate-100 font-sans cursor-default selection:bg-indigo-500/30">

      {/* Navbar/Header */}
      <nav className="fixed top-0 w-full z-50 bg-slate-950/50 backdrop-blur-xl border-b border-white/5 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 shrink-0 overflow-hidden rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 p-px">
              <div className="flex h-full w-full items-center justify-center rounded-[11px] bg-slate-950/90 backdrop-blur-3xl">
                <Mail className="h-5 w-5 text-indigo-400" />
              </div>
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Nexus<span className="font-light">Inbox</span>
            </span>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-xl border border-white/10">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Session:</span>
              <select
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="bg-transparent text-sm font-medium text-indigo-400 outline-none cursor-pointer focus:text-white transition-colors"
              >
                <option value="default_user" className="bg-slate-900">Personal (Default)</option>
                <option value="user_2" className="bg-slate-900">Work Account</option>
                <option value="guest" className="bg-slate-900">Guest Session</option>
              </select>
            </div>

            <div className="flex items-center gap-4 text-sm font-medium text-slate-400">
              <button className="hover:text-white transition-colors flex items-center gap-2"><LayoutDashboard className="w-4 h-4" /> Dashboard</button>
              <div className="w-px h-4 bg-slate-800"></div>
              <button className="hover:text-white transition-colors flex items-center gap-2"><Settings className="w-4 h-4" /> Settings</button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 pt-32 pb-20 grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* Left Column: Upload */}
        <div className="lg:col-span-4 space-y-6">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight mb-3">
              Intelligent Email <br className="hidden lg:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Categorization</span>
            </h1>
            <p className="text-slate-400 leading-relaxed text-lg">
              Upload your raw export CSV. Our AI assistant will instantly parse, classify, and recommend actions for your inbox.
            </p>
          </div>

          <Card className="border-0 bg-white/5 backdrop-blur-2xl shadow-2xl ring-1 ring-white/10 overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <CardHeader className="relative z-10 border-b border-white/5 pb-4">
              <CardTitle className="text-lg flex items-center gap-2 text-slate-100">
                <UploadCloud className="w-5 h-5 text-indigo-400" /> Data Ingestion
              </CardTitle>
              <CardDescription className="text-slate-400">Process your communication logs</CardDescription>
            </CardHeader>
            <CardContent className="p-6 relative z-10">
              <form onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
                <div
                  className={`
                    flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl transition-all duration-300
                    ${dragActive ? "border-indigo-500 bg-indigo-500/10" : "border-slate-700 hover:border-slate-500 bg-slate-900/50"}
                  `}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <label htmlFor="file-upload" className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      {selectedFile ? (
                        <>
                          <FileText className="w-10 h-10 text-indigo-400 mb-3" />
                          <p className="mb-2 text-sm text-slate-200 font-medium truncate max-w-[200px]">{selectedFile.name}</p>
                          <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB CSV File</p>
                        </>
                      ) : (
                        <>
                          <UploadCloud className="w-10 h-10 text-slate-500 mb-3 transition-colors group-hover:text-indigo-400" />
                          <p className="mb-2 text-sm text-slate-300"><span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop</p>
                          <p className="text-xs text-slate-500">CSV file required</p>
                        </>
                      )}
                    </div>
                    <input id="file-upload" type="file" accept=".csv" className="hidden" onChange={handleChange} />
                  </label>
                </div>
              </form>

              <div className="mt-6 flex flex-col gap-3">
                <div className="flex gap-3">
                  <Button
                    onClick={handleUpload}
                    disabled={!selectedFile || loading}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white border-0 shadow-lg shadow-indigo-500/25 transition-all h-12 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Processing...</>
                    ) : (
                      <><span className="mr-2">Analyze CSV Input</span> <ArrowRight className="w-4 h-4" /></>
                    )}
                  </Button>

                  {selectedFile && (
                    <Button
                      variant="outline"
                      onClick={() => setSelectedFile(null)}
                      disabled={loading}
                      className="h-12 w-12 p-0 border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl flex-shrink-0"
                    >
                      <RefreshCcw className="w-5 h-5" />
                    </Button>
                  )}
                </div>

                <div className="relative flex items-center py-2">
                  <div className="flex-grow border-t border-slate-700"></div>
                  <span className="flex-shrink-0 mx-4 text-slate-500 text-sm">or</span>
                  <div className="flex-grow border-t border-slate-700"></div>
                </div>

                <Button
                  onClick={handleFetchGmail}
                  disabled={loading}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition-all h-12 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Fetching...</>
                  ) : (
                    <><Mail className="w-4 h-4 mr-2" /> Fetch Directly from Gmail</>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8 flex flex-col h-full min-h-[500px]">
          <Card className="flex-1 border-0 bg-white/5 backdrop-blur-2xl shadow-2xl ring-1 ring-white/10 overflow-hidden flex flex-col">
            <CardHeader className="border-b border-white/5 px-6 py-5 shrink-0 bg-slate-950/20">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg text-slate-100 flex items-center gap-2">
                    Analysis Results
                    {emails.length > 0 && <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/20">{emails.length}</span>}
                  </CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-auto">
              {emails.length > 0 ? (
                <div className="min-w-[700px]">
                  <div className="grid grid-cols-12 gap-4 border-b border-white/5 px-6 py-4 text-xs font-semibold tracking-wider text-slate-400 uppercase bg-slate-950/40">
                    <div className="col-span-2">Sender</div>
                    <div className="col-span-3">Subject</div>
                    <div className="col-span-2">Category</div>
                    <div className="col-span-3">Recommended Action</div>
                    <div className="col-span-2">Status</div>
                  </div>
                  <div className="divide-y divide-white/5">
                    {emails.map((email, index) => (
                      <div key={index} className="grid grid-cols-12 gap-4 px-6 py-5 text-sm items-center hover:bg-white/[0.02] transition-colors border-b border-white/5 last:border-0">
                        <div className="col-span-2 font-medium text-slate-200 truncate pr-4" title={email.From || "Unknown"}>
                          {email.From || "Unknown"}
                        </div>
                        <div className="col-span-3 text-slate-300 truncate pr-4" title={email.Subject || "(No Subject)"}>
                          {email.Subject || "(No Subject)"}
                        </div>
                        <div className="col-span-2">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${getCategoryColor(email.Category)}`}>
                            {getCategoryIcon(email.Category)}
                            {email.Category || "Unknown"}
                          </span>
                        </div>
                        <div className="col-span-3 text-slate-400 text-sm italic pr-4">
                          {email.Agent_Action || "Processing..."}
                        </div>
                        <div className="col-span-2 flex gap-2">
                          {email.Agent_Action?.includes("AWAITING HUMAN APPROVAL") ? (
                            <div className="flex flex-col gap-2 w-full">
                              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white h-8 text-xs font-bold" onClick={() => handleHITL(email.thread_id, "approve")}>Approve</Button>
                              <div className="flex gap-1">
                                <Button size="sm" variant="outline" className="flex-1 h-7 text-[10px] border-white/10" onClick={() => handleHITL(email.thread_id, "deny")}>Deny</Button>
                                <Button size="sm" variant="outline" className="flex-1 h-7 text-[10px] border-white/10" onClick={() => {
                                  const feedback = prompt("What should I change?");
                                  if (feedback) handleHITL(email.thread_id, "edit", feedback);
                                }}>Edit</Button>
                              </div>
                            </div>
                          ) : (
                            <div className="text-slate-500 text-[10px] uppercase font-bold tracking-widest bg-white/5 px-2 py-1 rounded">Completed</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-500">
                  <div className="w-24 h-24 mb-6 rounded-3xl bg-slate-800/50 flex items-center justify-center border border-white/5 relative">
                    <div className="absolute inset-0 bg-indigo-500/20 blur-xl rounded-full"></div>
                    <Mail className="w-10 h-10 text-slate-600 relative z-10" />
                  </div>
                  <h3 className="text-xl font-medium text-slate-300 mb-2">Awaiting Data</h3>
                  <p className="max-w-md mx-auto text-slate-500">Upload an inbox CSV log from the left panel to instantly categorize and generate action items for your emails.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}