import cv2
import datetime
import imutils
import numpy as np
from centroidtracker import CentroidTracker
from itertools import combinations
import math 

protopath="MobileNetSSD_deploy.prototxt"
modelpath="MobileNetSSD_deploy.caffemodel"
detector=cv2.dnn.readNetFromCaffe(prototxt=protopath,caffeModel=modelpath)


tracker=CentroidTracker(maxDisappeared=80,maxDistance=90)

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

def non_max_supression_fast(boxes,overlapThresh):
    try:
        if len(boxes)==0:
            return[]
        if boxes.dtype.kind=="i":
            boxes=boxes.astype("float")

        pick=[]
        x1=boxes[:,0]
        y1=boxes[:,1]
        x2=boxes[:,2]
        y2=boxes[:,3]

        area=(x2-x1+1)*(y2-y1+1)
        idxs=np.argsort(y2)

        while len(idxs)>0:
            last=len(idxs)-1
            i=idxs[last]
            pick.append(i)
            xx1=np.maximum(x1[i],x1[idxs[:last]])
            yy1=np.maximum(y1[i],y1[idxs[:last]])
            xx2=np.minimum(x2[i],y2[idxs[:last]])
            yy2=np.minimum(y2[i],y2[idxs[:last]])

            w=np.maximum(0,xx2-xx1+1)
            h=np.maximum(0,yy2-yy1+1)

            overlap=(w*h)/area[idxs[:last]]
            idxs=np.delete(idxs,np.concatenate(([last],
                                                np.where(overlap>overlapThresh)[0])))

        return boxes[pick].astype("int")
    except Exception as e:
        print("Exception occurred in non_max_suppression:{}".format(e))


def main () :
    cap=cv2.VideoCapture("videos/testvideo2.mp4")
    fps_start=datetime.datetime.now()
    fps=0
    total_frames=0
    centroid_dict=dict()

    while True:
        ret, frame= cap.read()
        frame=imutils.resize(frame,width=600)
        total_frames=total_frames+1


        (H,W)=frame.shape[:2]

        blob=cv2.dnn.blobFromImage(frame,0.007843,(W,H),127.5)
        detector.setInput(blob)
        person_detections=detector.forward()


        rects=[]

        for i in np.arange(0,person_detections.shape[2]):
            confidence=person_detections[0,0,i,2]
            if confidence>0.5:
                idx=int(person_detections[0,0,i,1])

                if CLASSES[idx] !="person":
                    continue

                person_box= person_detections[0,0,i,3:7] * np.array([W,H,W,H])
                (startX,startY,endX,endY)=person_box.astype("int")
                rects.append(person_box)
        boundingboxes=np.array(rects)
        boundingboxes=boundingboxes.astype(int)
        rects=non_max_supression_fast(boundingboxes,0.3)

        
        objects = tracker.update(rects)
        for (objectId,bbox) in objects.items():
            x1,y1,x2,y2=bbox
            x1=int(x1)
            y1=int(y1)
            x2=int(x2)
            y2=int(y2)
            cX=int((x1+x2)/2.0)
            cY=int((y1+y2)/2.0)

            centroid_dict[objectId]=(cX,cY,x1,y1,x2,y2)
            
            
            #text="ID:{}".format(objectId)
            #cv2.putText(frame,text,(x1,y1-5),cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),1)

        red_zone_list=[]
        for (id1,p1),(id2,p2) in combinations(centroid_dict.items(),2):
            dx,dy=p1[0]-p2[0],p1[1]-p2[1]
            distance=math.sqrt(dx*dx+dy*dy)
            if distance<75.0:
                if id1 not in red_zone_list:
                    red_zone_list.append(id1)
                if id2 not in red_zone_list:
                    red_zone_list.append(id2)

        for id,box in centroid_dict.items():
            if id in red_zone_list:
                cv2.rectangle(frame,(box[2],box[3]),(box[4],box[5]),(0,0,255),2)
            else:
                cv2.rectangle(frame,(box[2],box[3]),(box[4],box[5]),(0,255,0),2)

        fps_and_time=datetime.datetime.now()
        time_diff=fps_and_time - fps_start
        if time_diff.seconds==0:
            fps=0.0
        else:
            fps=(total_frames/time_diff.seconds)

        fps_text="FPS:{:.2f}".format(fps)

        cv2.putText(frame,fps_text,(5,30),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),2)
        cv2.imshow("FPS",frame)
        key=cv2.waitKey(1)
        if key==ord('q'):
            break
    cv2.destroyAllWindows()
main()