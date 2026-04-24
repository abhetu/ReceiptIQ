import UploadCard from "../components/UploadCard";
import { uploadReceipt, uploadTransactions } from "../api";

export default function UploadsPage() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <UploadCard title="Receipt Upload" accept=".pdf,.png,.jpg,.jpeg" onUpload={uploadReceipt} />
      <UploadCard title="Bank CSV Upload" accept=".csv" onUpload={uploadTransactions} />
    </div>
  );
}
